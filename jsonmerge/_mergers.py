# vim:ts=4 sw=4 expandtab softtabstop=4
import re

def overwrite(merger, base, head, schema, meta, **kwargs):
    return head

def version(merger, base, head, schema, meta, limit=None, **kwargs):
    if base is None:
        base = []
    else:
        base = list(base)

    base.append(merger.add_meta(head, meta))
    if limit is not None:
	    base = base[-limit:]

    return base

def append(merger, base, head, schema, meta, **kwargs):
    if not merger.is_type(head, "array"):
        raise TypeError("Head for an 'append' merge strategy is not an array")

    if base is None:
        base = []
    else:
        base = list(base)

    base += head
    return base

def object_merge(merger, base, head, schema, meta, **kwargs):
    if not merger.is_type(head, "object"):
        raise TypeError("Head for an 'object' merge strategy is not an object")

    if base is None:
        base = {}
    else:
        base = dict(base)

    for k, v in head.items():

        subschema = None

        # get subschema for this element
        if schema is not None:
            p = schema.get('properties')
            if p is not None:
                subschema = p.get(k)

            if subschema is None:
                p = schema.get('patternProperties')
                if p is not None:
                    for pattern, s in p.items():
                        if re.search(pattern, k):
                            subschema = s

            if subschema is None:
                p = schema.get('additionalProperties')
                if p is not None:
                    subschema = p.get(k)

        base[k] = merger.descend(base.get(k), v, subschema, meta)

    return base
