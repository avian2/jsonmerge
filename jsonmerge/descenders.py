# vim:ts=4 sw=4 expandtab softtabstop=4
from jsonmerge.exceptions import HeadInstanceError, SchemaError
from jsonmerge.jsonvalue import JSONValue

class Descender(object):
    """Base class for descender classes.

    Descenders are similar to merge strategies, except that they only handle
    recursion into deeper schema structures and don't touch instances.
    """
    def descend_instance(self, walk, schema, base, head):
        return None

    def descend_schema(self, walk, schema):
        return None

class Ref(Descender):
    def __init__(self):
        self.refs_descended = set('#')

    def descend_instance(self, walk, schema, base, head):
        ref = schema.val.get("$ref")
        if ref is None:
            return None

        with walk.resolver.resolving(ref) as resolved:
            return walk.descend(JSONValue(resolved, ref), base, head)

    def descend_schema(self, walk, schema):
        ref = schema.val.get("$ref")
        if ref is None:
            return None

        if ref in self.refs_descended:
            return schema

        if walk.resolver.is_remote_ref(ref):
            return schema

        self.refs_descended.add(ref)

        with walk.resolver.resolving(ref) as resolved:

            rinstance = JSONValue(resolved, ref)
            if not walk.is_type(rinstance, 'object'):
                raise SchemaError("'$ref' does not point to an object", schema)

            result = walk.descend(rinstance)

            resolved.clear()
            resolved.update(result.val)

        return schema

class OneOf(Descender):
    def do_descend(self, schema):
        one_of = schema.get("oneOf")
        if one_of.is_undef():
            return False

        # If we have a strategy defined on this level, don't descend into
        # subschemas.
        if not schema.get("mergeStrategy").is_undef():
            return False

        return True

    def descend_instance(self, walk, schema, base, head):
        if not self.do_descend(schema):
            return None

        one_of = schema.get("oneOf")

        valid = []

        def is_valid(v, schema):
            if v.is_undef():
                return True
            else:
                return not list(walk.merger.validator.iter_errors(v.val, schema))

        for i, subschema in enumerate(one_of.val):
            base_valid = is_valid(base, subschema)
            head_valid = is_valid(head, subschema)

            if base_valid and head_valid:
                valid.append(i)

        if len(valid) == 0:
            raise HeadInstanceError("No element of 'oneOf' validates both base and head", head)

        if len(valid) > 1:
            raise HeadInstanceError("Multiple elements of 'oneOf' validate", head)

        i = valid[0]
        return walk.descend(one_of[i], base, head)

    def descend_schema(self, walk, schema):
        if not self.do_descend(schema):
            return None

        one_of = schema.get("oneOf")

        for i in range(len(one_of.val)):
            one_of[i] = walk.descend(one_of[i])

        return schema

class AnyOfAllOf(Descender):
    def descend(self, schema):
        allOf = schema.get("allOf")
        anyOf = schema.get("anyOf")
        if allOf.is_undef() and anyOf.is_undef():
            return None

        # We must have a strategy defined on this level, or we can't know which
        # subschema to descend to.
        if not schema.get("mergeStrategy").is_undef():
            return None

        raise SchemaError("Can't descend to 'allOf' and 'anyOf' keywords", schema)

    def descend_instance(self, walk, schema, base, head):
        return self.descend(schema)

    def descend_schema(self, walk, schema):
        return self.descend(schema)
