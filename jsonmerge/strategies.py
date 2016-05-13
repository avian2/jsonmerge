# vim:ts=4 sw=4 expandtab softtabstop=4
from jsonmerge.exceptions import HeadInstanceError, \
                                 BaseInstanceError, \
                                 SchemaError
from jsonmerge.jsonvalue import JSONValue
import jsonschema
import re

class Strategy(object):
    """Base class for merge strategies.
    """

    def merge(self, walk, base, head, schema, meta, **kwargs):
        """Merge head instance into base.

        walk -- WalkInstance object for the current context.
        base -- JSONValue being merged into.
        head -- JSONValue being merged.
        schema -- Schema used for merging (also JSONValue)
        meta -- Meta data, as passed to the Merger.merge() method.
        kwargs -- Dict with any extra options given in the 'mergeOptions'
        keyword

        Specific merge strategies should override this method to implement
        their behavior.

        The function should return the object resulting from the merge.

        Recursion into the next level, if necessary, is achieved by calling
        walk.descend() method.
        """
        raise NotImplemented

    def get_schema(self, walk, schema, meta, **kwargs):
        """Return the schema for the merged document.

        walk -- WalkSchema object for the current context.
        schema -- Original document schema.
        meta -- Schema for the meta data, as passed to the Merger.get_schema()
        method.
        kwargs -- Dict with any extra options given in the 'mergeOptions'
        keyword.

        Specific merge strategies should override this method to modify the
        document schema depending on the behavior of the merge() method.

        The function should return the schema for the object resulting from the
        merge.

        Recursion into the next level, if necessary, is achieved by calling
        walk.descend() method.

        Implementations should take care that all external schema references
        are resolved in the returned schema. This can be achieved by calling
        walk.resolve_refs() method.
        """
        raise NotImplemented

class Overwrite(Strategy):
    def merge(self, walk, base, head, schema, meta, **kwargs):
        return head

    def get_schema(self, walk, schema, meta, **kwargs):
        return walk.resolve_refs(schema)

class Version(Strategy):
    def merge(self, walk, base, head, schema, meta, limit=None, unique=None, ignoreDups=True, **kwargs):

        # backwards compatibility
        if unique is False:
            ignoreDups = False

        if base.is_undef():
            base = JSONValue(val=[], ref=base.ref)
        else:
            base = JSONValue(list(base.val), base.ref)

        if not ignoreDups or not base.val or base.val[-1]['value'] != head.val:
            base.val.append(walk.add_meta(head.val, meta))
            if limit is not None:
                base.val = base.val[-limit:]

        return base

    def get_schema(self, walk, schema, meta, limit=None, **kwargs):

        if meta is not None:
            item = dict(meta)
        else:
            item = {}

        if 'properties' not in item:
            item['properties'] = {}

        item['properties']['value'] = walk.resolve_refs(schema).val

        rv = {  "type": "array",
                "items": item }

        if limit is not None:
            rv['maxItems'] = limit

        return JSONValue(rv, schema.ref)

class Append(Strategy):
    def merge(self, walk, base, head, schema, meta, **kwargs):
        if not walk.is_type(head, "array"):
            raise HeadInstanceError("Head for an 'append' merge strategy is not an array")

        if base.is_undef():
            base = JSONValue([], base.ref)
        else:
            if not walk.is_type(base, "array"):
                raise BaseInstanceError("Base for an 'append' merge strategy is not an array")

            base = JSONValue(list(base.val), base.ref)

        base.val += head.val
        return base

    def get_schema(self, walk, schema, meta, **kwargs):
        schema.val.pop('maxItems', None)
        schema.val.pop('uniqueItems', None)

        return walk.resolve_refs(schema)


class ArrayMergeById(Strategy):
    def merge(self, walk, base, head, schema, meta, idRef="id", ignoreId=None, **kwargs):
        if not walk.is_type(head, "array"):
            raise HeadInstanceError("Head for an 'arrayMergeById' merge strategy is not an array")  # nopep8

        if base.is_undef():
            base = JSONValue([], base.ref)
        else:
            if not walk.is_type(base, "array"):
                raise BaseInstanceError("Base for an 'arrayMergeById' merge strategy is not an array")  # nopep8
            base = JSONValue(list(base.val), base.ref)

        subschema = schema.get('items')

        if walk.is_type(subschema, "array"):
            raise SchemaError("'arrayMergeById' not supported when 'items' is an array")

        def iter_index_key_item(jv):
            for i, item in enumerate(jv):
                try:
                    key = walk.resolver.resolve_fragment(item.val, idRef)
                except jsonschema.RefResolutionError:
                    continue

                yield i, key, item

        for i, key_1, item_1 in iter_index_key_item(head):
            for j, key_2, item_2 in iter_index_key_item(head):
                if j < i:
                    if key_1 == key_2:
                        raise HeadInstanceError("Id was not unique")
                else:
                    break

        for i, head_key, head_item in iter_index_key_item(head):

            if head_key == ignoreId:
                continue

            key_count = 0
            for j, base_key, base_item in iter_index_key_item(base):

                if base_key == head_key:
                    key_count += 1
                    # If there was a match, we replace with a merged item
                    base.val[j] = walk.descend(subschema, base_item, head_item, meta).val

            if key_count == 0:
                # If there wasn't a match, we append a new object
                base.val.append(walk.descend(subschema, JSONValue(undef=True), head_item, meta).val)
            if key_count > 1:
                raise BaseInstanceError("Id was not unique")

        return base

    def get_schema(self, walk, schema, meta, **kwargs):
        subschema = schema.get('items')

        # Note we're discarding the walk.descend() result here. This is because
        # it would de-reference the $ref if the subschema is a reference - i.e.
        # in the result it would replace the reference with the copy of the
        # target.
        #
        # But we want to keep the $ref and do the walk.descend() only on the target of the reference.
        #
        # This seems to work, but is an ugly workaround. walk.descend() should
        # be fixed instead to not dereference $refs when not necessary.
        walk.descend(subschema, meta)
        return schema


class ObjectMerge(Strategy):
    def merge(self, walk, base, head, schema, meta, **kwargs):
        if not walk.is_type(head, "object"):
            raise HeadInstanceError("Head for an 'object' merge strategy is not an object")

        if base.is_undef():
            base = JSONValue({}, base.ref)
        else:
            if not walk.is_type(base, "object"):
                raise BaseInstanceError("Base for an 'object' merge strategy is not an object")

            base = JSONValue(dict(base.val), base.ref)

        for k, v in head.items():

            subschema = JSONValue(undef=True)

            # get subschema for this element
            if not schema.is_undef():
                p = schema.get('properties')
                if not p.is_undef():
                    subschema = p.get(k)

                if subschema.is_undef():
                    p = schema.get('patternProperties')
                    if not p.is_undef():
                        for pattern, s in p.items():
                            if re.search(pattern, k):
                                subschema = s

                if subschema.is_undef():
                    p = schema.get('additionalProperties')
                    if not p.is_undef():
                        subschema = p

            base.val[k] = walk.descend(subschema, base.get(k), v, meta).val

        return base

    def get_schema(self, walk, schema, meta, **kwargs):

        for forbidden in ("oneOf", "allOf", "anyOf"):
            if forbidden in schema.val:
                raise SchemaError("Type ambiguous schema")

        schema2 = JSONValue(dict(schema.val), schema.ref)

        def descend_keyword(keyword):
            p = schema.get(keyword)
            if not p.is_undef():
                for k, v in p.items():
                    schema2.val[keyword][k] = walk.descend(v, meta).val

        descend_keyword("properties")
        descend_keyword("patternProperties")

        p = schema.get("additionalProperties")
        if not p.is_undef():
            schema2.val["additionalProperties"] = walk.descend(p, meta).val

        return schema2
