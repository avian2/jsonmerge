import re

def overwrite(merger, base, head, _schema, meta):
    return head

def version(merger, base, head, _schema, meta):
    if base is None:
        base = []
    else:
        base = list(base)

    base.append(merger.add_meta(head, meta))
    return base

def version_last(merger, base, head, _schema, meta):
    return merger.add_meta(head, meta)

def append(merger, base, head, _schema, meta):
    if base is None:
        base = []
    else:
        base = list(base)

    base += head
    return base

def object_merge(merger, base, head, _schema, meta):
    if base is None:
        base = {}
    else:
        base = dict(base)

    for k, v in head.iteritems():

        subschema = None

        # get subschema for this element
        p = _schema.get('properties')
        if p is not None:
            subschema = p.get(k)

        if subschema is None:
            p = _schema.get('patternProperties')
            if p is not None:
                for pattern, s in p.iteritems():
                    if re.search(pattern, k):
                        subschema = s

        if subschema is None:
            p = _schema.get('additionalProperties')
            if p is not None:
                subschema = p.get(k)

        base[k] = merger.descend(base.get(k), v, subschema, meta)

    return base
