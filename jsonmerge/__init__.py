import numbers
import _mergers
import pprint
from jsonschema.validators import Draft4Validator

class Merger(object):

    _mergers = {
        "overwrite": _mergers.overwrite,
        "version": _mergers.version,
        "versionLast": _mergers.version_last,
        "append": _mergers.append,
        "objectMerge": _mergers.object_merge,
    }

    def __init__(self, schema):
        self.schema = schema
        self.validator = Draft4Validator(schema)

    def merge(self, base, head, schema=None, meta=None):
        if schema is None:
            schema = self.schema

        return self.descend(base, head, schema, meta)

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
        else:
            name = None

        if name is None:
            if self.validator.is_type(head, "object"):
                name = "objectMerge"
            else:
                name = "overwrite"

        merger = self._mergers[name]
        return merger(self, base, head, schema, meta)


def merge(base, head, schema):
    merger = Merger(schema)
    return merger.merge(base, head)
