import numbers
import _mergers
import pprint

class UnknownType(Exception):
    def __init__(self, type, instance, schema):
        self.type = type
        self.instance = instance
        self.schema = schema

def flatten(suitable_for_isinstance):
    """
    isinstance() can accept a bunch of really annoying different types:
        * a single type
        * a tuple of types
        * an arbitrary nested tree of tuples

    Return a flattened tuple of the given argument.

    """

    types = set()

    if not isinstance(suitable_for_isinstance, tuple):
        suitable_for_isinstance = (suitable_for_isinstance,)
    for thing in suitable_for_isinstance:
        if isinstance(thing, tuple):
            types.update(flatten(thing))
        else:
            types.add(thing)
    return tuple(types)


class Merger(object):

    _types = {
        "array" : list, "boolean" : bool, "integer" : (int, long),
        "null" : type(None), "number" : numbers.Number, "object" : dict,
        "string" : str,
    }

    _mergers = {
        "overwrite": _mergers.overwrite,
        "version": _mergers.version,
        "append": _mergers.append,
        "objectMerge": _mergers.object_merge,
    }

    def __init__(self, schema):
        self.schema = schema

    def is_type(self, instance, type):
        if type not in self._types:
            raise UnknownType(type, instance, self.schema)

        pytypes = self._types[type]

        # bool inherits from int, so ensure bools aren't reported as ints
        if isinstance(instance, bool):
            pytypes = _utils.flatten(pytypes)
            is_number = any(
                issubclass(pytype, numbers.Number) for pytype in pytypes
            )
            if is_number and bool not in pytypes:
                return False
        return isinstance(instance, pytypes)

    def merge(self, base, head, schema=None):
        if schema is None:
            schema = self.schema

        return self.descend(base, head, schema)

    def descend(self, base, head, schema=None):

#        print "\n" + "="*50
#        print "base:",
#        pprint.pprint(base)
#        print "head:",
#        pprint.pprint(head)
#        print "schema:",
#        pprint.pprint(schema)

        if schema is not None:
            name = schema.get("mergeStrategy")
        else:
            name = None

        if name is None:
            if self.is_type(head, "object"):
                name = "objectMerge"
            else:
                name = "overwrite"

        merger = self._mergers[name]
        return merger(self, base, head, schema)


def merge(base, head, schema):
    merger = Merger(schema)
    return merger.merge(base, head)
