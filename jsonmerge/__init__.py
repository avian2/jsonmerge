import numbers
import _mergers
import pprint
from jsonschema.validators import Draft4Validator

class Merger(object):

    MERGERS = {
        "overwrite": _mergers.overwrite,
        "version": _mergers.version,
        "versionLast": _mergers.version_last,
        "append": _mergers.append,
        "objectMerge": _mergers.object_merge,
    }

    def __init__(self, schema):
        """Create a new Merger object.

        schema -- JSON schema to use when merging.
        """

        self.schema = schema
        self.validator = Draft4Validator(schema)

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
        else:
            name = None

        if name is None:
            if self.validator.is_type(head, "object"):
                name = "objectMerge"
            else:
                name = "overwrite"

        merger = self.MERGERS[name]
        return merger(self, base, head, schema, meta)


def merge(base, head, schema):
    merger = Merger(schema)
    return merger.merge(base, head)
