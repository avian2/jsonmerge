# vim:ts=4 sw=4 expandtab softtabstop=4
from jsonmerge.exceptions import HeadInstanceError
from jsonmerge.jsonvalue import JSONValue

def ref(walk, schema, *args):
    ref = schema.val.get("$ref")
    if ref is None:
        return None

    with walk.resolver.resolving(ref) as resolved:
        return walk.descend(JSONValue(resolved, ref), *args)

def oneOf(walk, schema, base, head, meta):
    one_of = schema.get("oneOf")
    if one_of.is_undef():
        return None

    valid = []

    for i, subschema in enumerate(one_of.val):
        if base.is_undef():
            base_valid = True
        else:
            base_valid = not list(walk.merger.validator.iter_errors(base.val, subschema))

        if head.is_undef():
            head_valid = True
        else:
            head_valid = not list(walk.merger.validator.iter_errors(head.val, subschema))

        if base_valid and head_valid:
            valid.append(i)

    if len(valid) == 0:
        raise HeadInstanceError("No element of 'oneOf' validates both head and base")

    if len(valid) > 1:
        raise HeadInstanceError("Multiple elements of 'oneOf' validate")

    i = valid[0]
    return walk.descend(one_of[i], base, head, meta)
