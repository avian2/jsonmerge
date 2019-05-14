# vim:ts=4 sw=4 expandtab softtabstop=4
from collections import OrderedDict
from jsonmerge.jsonvalue import JSONValue
from jsonmerge.resolver import LocalRefResolver
from jsonmerge import strategies
from jsonmerge import descenders
from jsonmerge.exceptions import SchemaError
from jsonschema.validators import Draft4Validator
import logging

log = logging.getLogger(name=__name__)

#logging.basicConfig(level=logging.DEBUG)

class Walk(object):

    DESCENDERS = [
            descenders.Ref,
            descenders.OneOf,
            descenders.AnyOfAllOf,
    ]

    def __init__(self, merger):
        self.merger = merger
        self.resolver = merger.validator.resolver
        self.lvl = -1

        self.descenders = [ cls() for cls in self.DESCENDERS ]

    def _indent(self):
        return "  " * self.lvl

    def is_type(self, instance, type):
        """Check if instance if a specific JSON type."""
        assert isinstance(instance, JSONValue)

        if instance.is_undef():
            return False

        return self.merger.validator.is_type(instance.val, type)

    def descend(self, schema, *args):
        assert isinstance(schema, JSONValue)
        self.lvl += 1

        log.debug("descend: %sschema %s" % (self._indent(), schema.ref,))

        if not schema.is_undef():
            with self.resolver.resolving(schema.ref) as resolved:
                assert schema.val is resolved

        if not schema.is_undef():

            for descender in self.descenders:
                rv = self.call_descender(descender, schema, *args)
                if rv is not None:
                    self.lvl -= 1
                    return rv

            name = schema.val.get("mergeStrategy")
            opts = schema.val.get("mergeOptions")
            if opts is None:
                opts = {}
        else:
            name = None
            opts = {}

        if name is None:
            name = self.default_strategy(schema, *args, **opts)

        log.debug("descend: %sinvoke strategy %s" % (self._indent(), name))

        try:
            strategy = self.merger.strategies[name]
        except KeyError:
            raise SchemaError("Unknown strategy '%s'" % name, schema)

        rv = self.work(strategy, schema, *args, **opts)

        self.lvl -= 1
        return rv

class WalkInstance(Walk):

    def __init__(self, merger, base, head):
        Walk.__init__(self, merger)
        self.base_resolver = LocalRefResolver("", base.val)
        self.head_resolver = LocalRefResolver("", head.val)

    def add_meta(self, head, meta):
        if meta is None:
            rv = dict()
        else:
            rv = dict(meta)

        rv['value'] = head
        return rv

    def default_strategy(self, schema, base, head, meta, **kwargs):
        if self.is_type(head, "object"):
            return "objectMerge"
        else:
            return "overwrite"

    def call_descender(self, descender, schema, base, head, meta):
        return descender.descend_instance(self, schema, base, head, meta)

    def work(self, strategy, schema, base, head, meta, **kwargs):
        assert isinstance(schema, JSONValue)
        assert isinstance(base, JSONValue)
        assert isinstance(head, JSONValue)

        log.debug("work   : %sbase %s, head %s" % (self._indent(), base.ref, head.ref))

        if not base.is_undef():
            with self.base_resolver.resolving(base.ref) as resolved:
                assert base.val is resolved

        if not head.is_undef():
            with self.head_resolver.resolving(head.ref) as resolved:
                assert head.val is resolved

        rv = strategy.merge(self, base, head, schema, meta, objclass_menu=self.merger.objclass_menu, **kwargs)

        assert isinstance(rv, JSONValue)
        return rv

class WalkSchema(Walk):

    def is_base_context(self):
        return self.resolver.base_uri == self.merger.schema.get('id', '')

    def resolve_refs(self, schema):
        # For backwards compatibility with jsonmerge <= 1.3.0
        return schema

    def _resolve_refs(self, schema, resolve_base=False):
        assert isinstance(schema, JSONValue)

        if (not resolve_base) and self.is_base_context():
            # no need to resolve refs in the context of the original schema - they 
            # are still valid
            return schema
        elif self.is_type(schema, "array"):
            return JSONValue([ self._resolve_refs(v).val for v in schema ], schema.ref)
        elif self.is_type(schema, "object"):
            ref = schema.val.get("$ref")
            if ref is not None:
                with self.resolver.resolving(ref) as resolved:
                    return self._resolve_refs(JSONValue(resolved, ref))
            else:
                return JSONValue(dict( ((k, self._resolve_refs(v).val) for k, v in schema.items()) ), schema.ref)
        else:
            return schema

    def schema_is_object(self, schema):

        objonly = (
                'maxProperties',
                'minProperties',
                'required',
                'additionalProperties',
                'properties',
                'patternProperties',
                'dependencies')

        for k in objonly:
            if k in schema.val:
                return True

        if schema.val.get('type') == 'object':
            return True

        return False

    def default_strategy(self, schema, meta, **kwargs):

        if self.schema_is_object(schema):
            return "objectMerge"
        else:
            return "overwrite"

    def call_descender(self, descender, schema, meta):
        return descender.descend_schema(self, schema, meta)

    def work(self, strategy, schema, meta, **kwargs):
        assert isinstance(schema, JSONValue)

        schema = JSONValue(dict(schema.val), schema.ref)
        schema.val.pop("mergeStrategy", None)
        schema.val.pop("mergeOptions", None)

        rv = strategy.get_schema(self, schema, meta, **kwargs)
        assert isinstance(rv, JSONValue)
        return rv

class Merger(object):

    STRATEGIES = {
        "discard": strategies.Discard(),
        "overwrite": strategies.Overwrite(),
        "version": strategies.Version(),
        "append": strategies.Append(),
        "objectMerge": strategies.ObjectMerge(),
        "arrayMergeById": strategies.ArrayMergeById()
    }

    def __init__(self, schema, strategies=(), objclass_def='dict', objclass_menu=None,
            validatorclass=Draft4Validator):
        """Create a new Merger object.

        schema -- JSON schema to use when merging.
        strategies -- Any additional merge strategies to use during merge.
        objclass_def -- Name of the default class for JSON objects.
        objclass_menu -- Any additional classes for JSON objects.
        validatorclass -- JSON Schema validator class.

        strategies argument should be a dict mapping strategy names to
        instances of Strategy subclasses.

        objclass_def specifies the default class used for JSON objects when one
        is not specified in the schema. It should be 'dict' (dict built-in),
        'OrderedDict' (collections.OrderedDict) or one of the names specified
        in the objclass_menu argument. If not specified, 'dict' is used.

        objclass_menu argument should be a dictionary that maps a string name
        to a function or class that will return an empty dictionary-like object
        to use as a JSON object. The function must accept either no arguments
        or a dictionary-like object.

        validatorclass argument can be used to supply a validator class from
        jsonschema. This can be used for example to specify which JSON Schema
        draft version will be used during merge.
        """

        self.schema = schema

        if hasattr(validatorclass, 'ID_OF'):
            resolver = LocalRefResolver.from_schema(schema, id_of=validatorclass.ID_OF)
        else:
            # jsonschema<3.0.0
            resolver = LocalRefResolver.from_schema(schema)
        self.validator = validatorclass(schema, resolver=resolver)

        self.strategies = dict(self.STRATEGIES)
        self.strategies.update(strategies)

        self.objclass_menu = { 'dict': dict, 'OrderedDict': OrderedDict }
        if objclass_menu:
            self.objclass_menu.update(objclass_menu)

        self.objclass_menu['_default'] = self.objclass_menu[objclass_def]

    def cache_schema(self, schema, uri=None):
        """Cache an external schema reference.

        schema -- JSON schema to cache
        uri -- Optional URI for the schema

        If the JSON schema for merging contains external references, they will
        be fetched using HTTP from their respective URLs. Alternatively, this
        method can be used to pre-populate the cache with any external schemas
        that are already known.

        If URI is omitted, it is obtained from the schema itself ('id' or '$id'
        keyword, depending on the JSON Schema draft used)
        """

        if uri is None:
            if hasattr(self.validator, 'ID_OF'):
                uri = self.validator.ID_OF(schema)
            else:
                # jsonschema<3.0.0
                uri = schema.get('id', '')

        self.validator.resolver.store.update(((uri, schema),))

    def merge(self, base, head, meta=None):
        """Merge head into base.

        base -- Old JSON document you are merging into.
        head -- New JSON document for merging into base.
        meta -- Optional dictionary with meta-data.

        Any elements in the meta dictionary will be added to
        the dictionaries appended by the version strategies.

        Returns an updated base document
        """

        schema = JSONValue(self.schema)

        if base is None:
            base = JSONValue(undef=True)
        else:
            base = JSONValue(base)

        head = JSONValue(head)

        walk = WalkInstance(self, base, head)
        return walk.descend(schema, base, head, meta).val

    def get_schema(self, meta=None):
        """Get JSON schema for the merged document.

        meta -- Optional JSON schema for the meta-data.

        Returns a JSON schema for documents returned by the
        merge() method.
        """

        if meta is not None:

            # This is kind of ugly - schema for meta data
            # can again contain references to external schemas.
            #
            # Since we already have in place all the machinery
            # to resolve these references in the merge schema,
            # we (ab)use it here to do the same for meta data
            # schema.
            m = Merger(meta)
            m.validator.resolver.store.update(self.validator.resolver.store)

            w = WalkSchema(m)
            meta = w._resolve_refs(JSONValue(meta), resolve_base=True).val

        schema = JSONValue(self.schema)

        walk = WalkSchema(self)
        return walk.descend(schema, meta).val

def merge(base, head, schema={}):
    """Merge two JSON documents using strategies defined in schema.

    base -- Old JSON document you are merging into.
    head -- New JSON document for merging into base.
    schema -- JSON schema to use when merging.

    Merge strategy for each value can be specified in the schema
    using the "mergeStrategy" keyword. If not specified, default
    strategy is to use "objectMerge" for objects and "overwrite"
    for all other types.
    """

    merger = Merger(schema)
    return merger.merge(base, head)
