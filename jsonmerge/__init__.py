# vim:ts=4 sw=4 expandtab softtabstop=4
import numbers
import pprint

from jsonmerge import strategies
from jsonschema.validators import Draft4Validator

class Merger(object):

    STRATEGIES = {
        "overwrite": strategies.Overwrite(),
        "version": strategies.Version(),
        "append": strategies.Append(),
        "objectMerge": strategies.ObjectMerge(),
    }

    def __init__(self, schema):
        """Create a new Merger object.

        schema -- JSON schema to use when merging.
        """

        self.schema = schema
        self.validator = Draft4Validator(schema)

    def is_type(self, instance, type):
        return self.validator.is_type(instance, type)

    def merge(self, base, head, meta=None):
        """Merge head into base.

        base -- Old JSON document you are merging into.
        head -- New JSON document for merging into base.
        meta -- Dictionary with meta-data.

        Any elements in the meta dictionary will be added to
        the dictionaries appended by the version strategies.

        Returns an updated base document
        """

        return self.descend(base, head, self.schema, meta)

    def add_meta(self, head, meta):
        if meta is None:
            rv = dict()
        else:
            rv = dict(meta)

        rv['value'] = head
        return rv

    def descend(self, base, head, schema, meta):

#        print "\n" + "="*50
#        print "base:",
#        pprint.pprint(base)
#        print "head:",
#        pprint.pprint(head)
#        print "schema:",
#        pprint.pprint(schema)

        if schema is not None:
            ref = schema.get("$ref")
            if ref is not None:
                with self.validator.resolver.resolving(ref) as resolved:
                    return self.descend(base, head, resolved, meta)
            else:
                name = schema.get("mergeStrategy")
                kwargs = schema.get("mergeOptions")
                if kwargs is None:
                    kwargs = {}
        else:
            name = None
            kwargs = {}

        if name is None:
            if self.is_type(head, "object"):
                name = "objectMerge"
            else:
                name = "overwrite"

        strategy = self.STRATEGIES[name]
        return strategy.merge(self, base, head, schema, meta, **kwargs)

    def get_schema(self):
        return self.descend_schema(self.schema)

    def descend_schema(self, schema):

#        print "\n" + "="*50
#        print "base:",
#        pprint.pprint(base)
#        print "head:",
#        pprint.pprint(head)
#        print "schema:",
#        pprint.pprint(schema)

        if schema is not None:
            ref = schema.get("$ref")
            if ref is not None:
                with self.validator.resolver.resolving(ref) as resolved:
                    return self.descend_schema(resolved)
            else:
                name = schema.get("mergeStrategy")
                kwargs = schema.get("mergeOptions")
                if kwargs is None:
                    kwargs = {}
        else:
            name = None
            kwargs = {}

        if name is None:
            # FIXME: get expected type from schema
            raise TypeError
            #if self.is_type(head, "object"):
            #    name = "objectMerge"
            #else:
            #    name = "overwrite"

        strategy = self.STRATEGIES[name]
        return strategy.get_schema(self, schema, **kwargs)

def merge(base, head, schema):
    merger = Merger(schema)
    return merger.merge(base, head)
