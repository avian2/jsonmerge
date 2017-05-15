# vim:ts=4 sw=4 expandtab softtabstop=4
import unittest

from collections import OrderedDict
import jsonmerge
import jsonmerge.strategies
from jsonmerge.exceptions import (
    HeadInstanceError,
    BaseInstanceError,
    SchemaError
)
from jsonmerge.jsonvalue import JSONValue

import jsonschema


class TestMerge(unittest.TestCase):

    def test_default(self):

        schema = {}

        base = None
        base = jsonmerge.merge(base, "a", schema)
        base = jsonmerge.merge(base, "b", schema)

        self.assertEqual(base, "b")

    def test_overwrite(self):

        schema = {'mergeStrategy': 'overwrite'}

        base = None
        base = jsonmerge.merge(base, "a", schema)
        base = jsonmerge.merge(base, "b", schema)

        self.assertEqual(base, "b")

    def test_version(self):

        schema = {'mergeStrategy': 'version'}

        base = None
        base = jsonmerge.merge(base, "a", schema)
        base = jsonmerge.merge(base, "b", schema)

        self.assertEqual(base, [{'value': "a"}, {'value': "b"}])

    def test_version_does_not_duplicate(self):
        # Don't record change if it didn't change

        schema = {'mergeStrategy': 'version'}

        base = None
        base = jsonmerge.merge(base, "a", schema)
        base = jsonmerge.merge(base, "b", schema)
        base = jsonmerge.merge(base, "b", schema)

        self.assertEqual(base, [{'value': "a"}, {'value': "b"}])

    def test_version_meta(self):

        schema = {'mergeStrategy': 'version'}

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, "a", meta={'uri': 'http://example.com/a'})
        base = merger.merge(base, "b", meta={'uri': 'http://example.com/b'})

        self.assertEqual(base, [
            {'value': "a",
             'uri': 'http://example.com/a'},
            {'value': "b",
             'uri': 'http://example.com/b'}])

    def test_version_ignoredups_false(self):

        schema = {'mergeStrategy': 'version',
                  'mergeOptions': {'ignoreDups': False}}

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, "a")
        base = merger.merge(base, "a")

        self.assertEqual(base, [{'value': "a"}, {'value': "a"}])

    def test_version_unique_false(self):

        schema = {'mergeStrategy': 'version',
                  'mergeOptions': {'unique': False}}

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, "a")
        base = merger.merge(base, "a")

        self.assertEqual(base, [{'value': "a"}, {'value': "a"}])

    def test_version_ignoredups_true(self):

        schema = {'mergeStrategy': 'version'}

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, "a")
        base = merger.merge(base, "a")

        self.assertEqual(base, [{'value': "a"}])

    def test_version_last(self):

        schema = {'mergeStrategy': 'version',
                  'mergeOptions': {'limit': 1}}

        base = None
        base = jsonmerge.merge(base, "a", schema)
        base = jsonmerge.merge(base, "b", schema)

        self.assertEqual(base, [{'value': "b"}])

    def test_append(self):
        schema = {'mergeStrategy': 'append'}

        base = None
        base = jsonmerge.merge(base, ["a"], schema)
        base = jsonmerge.merge(base, ["b"], schema)

        self.assertEqual(base, ["a", "b"])

    def test_append_type_error(self):

        schema = {'mergeStrategy': 'append'}

        base = None
        self.assertRaises(HeadInstanceError,
                          jsonmerge.merge, base, "a", schema)

    def test_append_type_error_base(self):

        schema = {'mergeStrategy': 'append'}

        base = "ab"
        self.assertRaises(BaseInstanceError,
                          jsonmerge.merge, base, ["a"], schema)

    def test_merge_default(self):
        schema = {}
        base = None
        base = jsonmerge.merge(base, {'a': "a"}, schema)
        base = jsonmerge.merge(base, {'b': "b"}, schema)

        self.assertEqual(base, {'a': "a", 'b': "b"})

    def test_merge_empty_schema(self):

        schema = {}

        base = None
        base = jsonmerge.merge(base, {'a': {'b': 'c'}}, schema)

        self.assertEqual(base, {'a': {'b': 'c'}})

    def test_merge_trivial(self):

        schema = {'mergeStrategy': 'objectMerge'}

        base = None
        base = jsonmerge.merge(base, {'a': "a"}, schema)
        base = jsonmerge.merge(base, {'b': "b"}, schema)

        self.assertTrue(isinstance(base, dict))
        self.assertEqual(base, {'a': "a", 'b': "b"})

    def test_merge_null(self):

        schema = {'mergeStrategy': 'objectMerge'}

        base = {'a': 'a'}
        head = {'a': None}

        r = jsonmerge.merge(base, head, schema)

        self.assertEqual(head, r)

    def test_merge_type_error(self):

        schema = {'mergeStrategy': 'objectMerge'}

        base = None
        self.assertRaises(HeadInstanceError,
                          jsonmerge.merge, base, "a", schema)

    def test_merge_type_error_base(self):

        schema = {'mergeStrategy': 'objectMerge'}

        base = "ab"
        self.assertRaises(BaseInstanceError,
                          jsonmerge.merge, base, {'foo': 1}, schema)

    def test_merge_overwrite(self):

        schema = {'mergeStrategy': 'objectMerge'}

        base = None
        base = jsonmerge.merge(base, {'a': "a"}, schema)
        base = jsonmerge.merge(base, {'a': "b"}, schema)

        self.assertEqual(base, {'a': "b"})

    def test_merge_objclass(self):
        schema = {'mergeStrategy': 'objectMerge', 'mergeOptions': { 'objClass': 'OrderedDict'}}

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, OrderedDict([('c', "a"), ('a', "a")]), schema)
        self.assertIsInstance(base, OrderedDict)
        self.assertEqual([k for k in base], ['c', 'a'])

        base = merger.merge(base, {'a': "b"}, schema)
        self.assertIsInstance(base, OrderedDict)
        self.assertEqual([k for k in base], ['c', 'a'])

        self.assertEqual(base, {'a': "b", 'c': "a"})

    def test_merge_objclass2(self):
        schema = {'mergeStrategy': 'objectMerge',
                  'properties': {
                      'a': {'mergeStrategy': 'objectMerge',
                            'mergeOptions': { 'objClass': 'OrderedDict'}}}}

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, {'a': {'b': 'c'}, 'd': {'e': 'f'}}, schema)

        self.assertIsInstance(base, dict)
        self.assertIsInstance(base['a'], OrderedDict)
        self.assertIsInstance(base['d'], dict)

    def test_merge_objclass_bad_cls(self):
        schema = {'mergeStrategy': 'objectMerge', 'mergeOptions': { 'objClass': 'foo'}}

        merger = jsonmerge.Merger(schema)

        base = None
        self.assertRaises(SchemaError, merger.merge, base, OrderedDict([('c', "a"), ('a', "a")]), schema)

    def test_merge_objclass_menu(self):
        schema = {'mergeStrategy': 'objectMerge', 'mergeOptions': { 'objClass': 'foo'}}

        class MyDict(dict):
            pass

        objclass_menu = {'foo': MyDict}

        merger = jsonmerge.Merger(schema, objclass_menu=objclass_menu)

        base = None
        base = merger.merge(base, {'c': "a", 'a': "a"}, schema)

        self.assertTrue(isinstance(base, MyDict))

    def test_merge_objclass_def(self):
        schema = {'mergeStrategy': 'objectMerge'}

        merger = jsonmerge.Merger(schema, objclass_def='OrderedDict')

        base = None
        base = merger.merge(base, OrderedDict([('c', "a"), ('a', "a")]), schema)
        self.assertIsInstance(base, OrderedDict)
        self.assertEqual([k for k in base], ['c', 'a'])

        base = merger.merge(base, {'a': "b"}, schema)
        self.assertIsInstance(base, OrderedDict)
        self.assertEqual([k for k in base], ['c', 'a'])

        self.assertEqual(base, {'a': "b", 'c': "a"})

    def test_merge_append(self):

        schema = {'mergeStrategy': 'objectMerge',
                  'properties': {
                      'a': {'mergeStrategy': 'append'}
                  }}

        base = None
        base = jsonmerge.merge(base, {'a': ["a"]}, schema)
        base = jsonmerge.merge(base, {'a': ["b"], 'b': 'c'}, schema)

        self.assertEqual(base, {'a': ["a", "b"], 'b': 'c'})

    def test_merge_append_pattern(self):

        schema = {'mergeStrategy': 'objectMerge',
                  'patternProperties': {
                      'a': {'mergeStrategy': 'append'}
                  }}

        base = None
        base = jsonmerge.merge(base, {'a': ["a"]}, schema)
        base = jsonmerge.merge(base, {'a': ["b"], 'b': 'c'}, schema)

        self.assertEqual(base, {'a': ["a", "b"], 'b': 'c'})

    def test_merge_append_additional(self):

        schema = {'mergeStrategy': 'objectMerge',
                  'properties': {
                      'b': {'mergeStrategy': 'overwrite'}
                  },
                  'additionalProperties': {
                      'mergeStrategy': 'append'
                  }}

        base = None
        base = jsonmerge.merge(base, {'a': ["a"]}, schema)
        base = jsonmerge.merge(base, {'a': ["b"], 'b': 'c'}, schema)

        self.assertEqual(base, {'a': ["a", "b"], 'b': 'c'})

    def test_example(self):

        head1 = {
            'buyer': {
                'id': {
                    'name': "Test old",
                },
                'uri': 'Test uri old',
            }
        }

        head2 = {
            'buyer': {
                'id': {
                    'name': "Test new"
                },
                'uri': 'Test uri new',
            },

            'award': "Award"
        }

        base_expect = {
            'buyer': {
                'id': {
                    'name': [
                        {'value': "Test old"},
                        {'value': "Test new"},
                    ]
                },
                'uri': 'Test uri new',
            },

            'award': "Award"
        }

        schema = {
            'mergeStrategy': 'objectMerge',
            'properties': {
                'buyer': {
                    'properties': {
                        'id': {
                            'properties': {
                                'name': {
                                    'mergeStrategy': 'version',
                                }
                            }
                        },
                        'uri': {
                            'mergeStrategy': 'overwrite',
                        }
                    },
                },
                'award': {
                    'mergeStrategy': 'overwrite',
                }
            },
        }

        base = None
        base = jsonmerge.merge(base, head1, schema)
        base = jsonmerge.merge(base, head2, schema)

        self.assertEqual(base, base_expect)

    def test_refs(self):

        schema = {
            'properties': {
                'a': {'$ref': "#/definitions/a"},
            },
            'definitions': {
                "a": {
                    "properties": {
                        "b": {'mergeStrategy': 'version'},
                    }
                },
            }
        }

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, {"a": {"b": "c"}})
        base = merger.merge(base, {"a": {"b": "d"}})

        self.assertEqual(base, {"a": {"b": [{"value": "c"}, {"value": "d"}]}})

    def test_oneof(self):

        schema = {
            'oneOf': [
                {
                    'type': 'array',
                    'mergeStrategy': 'append'
                },
                {
                    'type': 'object'
                }
            ]
        }

        merger = jsonmerge.Merger(schema)

        base = [1]
        base = merger.merge(base, [2])

        self.assertEqual(base, [1,2])

        base = {'a': 1}
        base = merger.merge(base, {'b': 2})

        self.assertEqual(base, {'a': 1, 'b': 2})

        base = [1]
        self.assertRaises(HeadInstanceError, merger.merge, base, {'b': 2})

    def test_oneof_recursive(self):
        # Schema to merge all arrays with "append" strategy and all objects
        # with the default "objectMerge" strategy.

        schema = {
            "oneOf": [
                {
                    "type": "array",
                    "mergeStrategy": "append"
                },
                {
                    "type": "object",
                    "additionalProperties": {
                        "$ref": "#"
                    }
                },
                {
                    "type": "string"
                },
            ]
        }

        base = {"a": ["1"], "b": "3", "c": {"d": ["4"], "e": "f"}}
        head = {"a": ["2"], "b": "4", "g": "7", "c": {"d": ["3"]}}

        merger = jsonmerge.Merger(schema)
        base = merger.merge(base, head)

        self.assertEqual(base, {"a": ["1", "2"], "b": "4", "g": "7", "c": {"d": ["4", "3"], "e": "f"}})

    def test_custom_strategy(self):

        schema = {'mergeStrategy': 'myStrategy'}

        class MyStrategy(jsonmerge.strategies.Strategy):
            def merge(self, walk, base, head, schema, meta, **kwargs):
                if base is None:
                    ref = ""
                else:
                    ref = base.ref

                return JSONValue("foo", ref)

        merger = jsonmerge.Merger(schema=schema,
                                  strategies={'myStrategy': MyStrategy()})

        base = None
        base = merger.merge(base, {'a': 1})

        self.assertEqual(base, "foo")

    def test_merge_by_id(self):
        schema = {
            "properties": {
                "awards": {
                    "type": "array",
                    "mergeStrategy": "arrayMergeById",
                    "items": {
                        "properties": {
                            "id": {"type": "string"},
                            "field": {"type": "number"},
                        }
                    }
                }
            }
        }

        a = {
            "awards": [
                {"id": "A", "field": 1},
                {"id": "B", "field": 2}
            ]
        }

        b = {
            "awards": [
                {"id": "B", "field": 3},
                {"id": "C", "field": 4}
            ]
        }

        expected = {
            "awards": [
                {"id": "A", "field": 1},
                {"id": "B", "field": 3},
                {"id": "C", "field": 4}
            ]
        }

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, a)
        base = merger.merge(base, b)

        self.assertEqual(base, expected)

    def test_merge_by_id_when_key_is_empty_should_do_nothing(self):
        schema = {
            "properties": {
                "awards": {
                    "type": "array",
                    "mergeStrategy": "arrayMergeById",
                    "mergeOptions": {"ignoreId": ""},
                    "items": {
                        "properties": {
                            "id": {"type": "string"},
                            "field": {"type": "number"},
                        }
                    }
                }
            }
        }

        a = {
            "awards": [
                {"id": "A", "field": 1},
                {"id": "", "field": ""}
            ]
        }

        b = {
            "awards": [
                {"id": "B", "field": 3},
                {"id": "C", "field": 4}
            ]
        }

        expected = {
            "awards": [
                {"id": "A", "field": 1},
                {"id": "B", "field": 3},
                {"id": "C", "field": 4}
            ]
        }

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, a)
        base = merger.merge(base, b)

        self.assertEqual(base, expected)

    def test_merge_by_id_no_items(self):
        schema = {
            "mergeStrategy": "arrayMergeById",
            "mergeOptions": {"idRef": "id"},
        }

        a = [
            {"id": "A", "field": 1},
        ]

        b = [
            {"id": "A", "field": 2},
        ]

        # by default, it should fall back to "replace" strategy for integers.
        expected = [
            {"id": "A", "field": 2},
        ]

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, a)
        base = merger.merge(base, b)

        self.assertEqual(base, expected)

    def test_merge_by_id_simple_ref(self):
        schema = {
            "mergeStrategy": "arrayMergeById",
            "mergeOptions": {"idRef": "key"}
        }

        a = [
            {"key": "A", "field": 1},
        ]

        b = [
            {"key": "A", "field": 2},
        ]

        expected = [
            {"key": "A", "field": 2},
        ]

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, a)
        base = merger.merge(base, b)

        self.assertEqual(base, expected)

    def test_merge_by_id_no_key(self):
        schema = {
            "mergeStrategy": "arrayMergeById",
        }

        a = [
            {"id": "A", "field": 1},
        ]

        b = [
            {'field': 2}
        ]

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, a)
        base = merger.merge(base, b)

        # it should ignore array elements that do not have the id
        self.assertEqual(base, a)

    def test_merge_by_id_compex_ref(self):
        schema = {
            "mergeStrategy": "arrayMergeById",
            "mergeOptions": {"idRef": "/foo/bar"},
        }

        a = [
            {'foo': {'bar': 1}, 'baz': 1}
        ]

        b = [
            {'foo': {'bar': 2}}
        ]

        c = [
            {'foo': {'bar': 1}, 'baz': 2}
        ]

        # by default, it should fall back to "replace" strategy for integers.
        expected = [
            {'foo': {'bar': 1}, 'baz': 2},
            {'foo': {'bar': 2}}
        ]

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, a)
        base = merger.merge(base, b)
        base = merger.merge(base, c)

        self.assertEqual(base, expected)

    def test_merge_by_id_with_complex_array(self):
        schema = {
            "properties": {
                "awards": {
                    "type": "array",
                    "mergeStrategy": "arrayMergeById",
                    "items": {
                        "properties": {
                            "id": {"type": "string"},
                            "field": {
                                "type": "array",
                                "items": {
                                    "properties": {
                                        "xx": {
                                            "type": "string"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        a = {
            "awards": [
                {"id": "A", "field": [{"xx": "testA1"}, {"xx": "testA2"}]},
                {"id": "B", "field": [{"xx": "testA3"}, {"xx": "testA4"}]}
            ]
        }

        b = {
            "awards": [
                {"id": "B", "field": [{"xx": "testA3"}, {"xx": "testA6"}]},
                {"id": "C", "field": [{"xx": "testA7"}, {"xx": "testA8"}]}
            ]
        }

        expected = {
            "awards": [
                {"id": "A", "field": [{"xx": "testA1"}, {"xx": "testA2"}]},
                {"id": "B", "field": [{"xx": "testA3"}, {"xx": "testA6"}]},
                {"id": "C", "field": [{"xx": "testA7"}, {"xx": "testA8"}]}
            ]
        }

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, a)
        base = merger.merge(base, b)

        self.assertEqual(base, expected)

    def test_merge_by_id_with_subschema(self):
        schema = {
            "properties": {
                "awards": {
                    "type": "array",
                    "mergeStrategy": "arrayMergeById",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string"
                            },
                            "field": {
                                "type": "number",
                                "mergeStrategy": "version"
                            }
                        }
                    }
                }
            }
        }

        a = {
            "awards": [
                {"id": "A", "field": 1},
                {"id": "B", "field": 2}
            ]
        }

        b = {
            "awards": [
                {"id": "B", "field": 3},
                {"id": "C", "field": 4}
            ]
        }

        expected = {
            "awards": [
                {"id": "A", "field": [{"value": 1}]},
                {"id": "B", "field": [{"value": 2}, {"value": 3}]},
                {"id": "C", "field": [{"value": 4}]}
            ]
        }

        merger = jsonmerge.Merger(schema)

        base = None
        base = merger.merge(base, a)
        base = merger.merge(base, b)

        self.assertEqual(base, expected)

    def test_merge_by_id_items_array(self):
        schema = {
            "mergeStrategy": "arrayMergeById",
            "items": [
                {},
                {},
            ]
        }

        head = [
            {'id': 'A'},
            {'id': 'B'}
        ]

        merger = jsonmerge.Merger(schema)

        base = None
        self.assertRaises(SchemaError, merger.merge, base, head)

    def test_merge_by_id_only_integers(self):

        # arrayMergeById strategy can be used to treat simple arrays of
        # integers as Python sets by setting idRef to root (i.e. pointing to
        # the array element itself)
        #
        # https://github.com/avian2/jsonmerge/issues/24

        schema = {
            "mergeStrategy": "arrayMergeById",
            "mergeOptions": {"idRef": "/"},
        }

        base = [ 1, 2 ]
        head = [ 2, 3 ]

        expected = [ 1, 2, 3]

        merger = jsonmerge.Merger(schema)

        base = merger.merge(base, head)

        self.assertEqual(base, expected)

    def test_merge_by_id_bad_head_type(self):
        schema = {
            'mergeStrategy': 'arrayMergeById'
        }

        head = {'foo': 'bar'}
        base = []

        merger = jsonmerge.Merger(schema)
        self.assertRaises(HeadInstanceError, merger.merge, base, head)

    def test_merge_by_id_bad_base_type(self):
        schema = {
            'mergeStrategy': 'arrayMergeById'
        }

        head = []
        base = {'foo': 'bar'}

        merger = jsonmerge.Merger(schema)
        self.assertRaises(BaseInstanceError, merger.merge, base, head)

    def test_merge_by_id_no_base_id(self):
        schema = {
            'mergeStrategy': 'arrayMergeById'
        }

        head = [ {'id': 'a'} ]
        base = [ {} ]

        merger = jsonmerge.Merger(schema)
        r = merger.merge(base, head)

        self.assertEqual(r, [ {}, {'id': 'a'} ])

    def test_merge_by_id_non_unique_base(self):
        schema = {
            "mergeStrategy": "arrayMergeById",
        }

        base = [
            {'id': 'a'},
            {'id': 'a'}
        ]

        head = [
            {'id': 'a',
             'foo': 1}
        ]

        merger = jsonmerge.Merger(schema)

        self.assertRaises(BaseInstanceError, merger.merge, base, head)

    def test_merge_by_id_non_unique_head(self):
        schema = {
            "mergeStrategy": "arrayMergeById",
        }

        base = [
            {'id': 'a',
             'foo': 1},
        ]

        head = [
            {'id': 'a',
             'foo': 2},
            {'id': 'a',
             'foo': 3}
        ]

        merger = jsonmerge.Merger(schema)

        self.assertRaises(HeadInstanceError, merger.merge, base, head)

    def test_append_with_maxitems(self):

        schema = {
            "mergeStrategy": "append",
            "maxItems": 2,
        }

        merger = jsonmerge.Merger(schema)

        head = ["a"]
        base = None

        base = merger.merge(base, head)
        base = merger.merge(base, head)
        base = merger.merge(base, head)

        schema2 = merger.get_schema()

        jsonschema.validate(head, schema2)
        jsonschema.validate(base, schema2)

    def test_append_with_unique(self):

        schema = {
            "mergeStrategy": "append",
            "uniqueItems": True,
        }

        merger = jsonmerge.Merger(schema)

        head = ["a"]
        base = None

        base = merger.merge(base, head)
        base = merger.merge(base, head)

        schema2 = merger.get_schema()

        jsonschema.validate(head, schema2)
        jsonschema.validate(base, schema2)

    def test_slash_in_property_name(self):

        base = {'a': 0}
        head = {'b': {'c/d': 1}}

        base = jsonmerge.merge(base, head)

        self.assertEqual(base, {'a': 0, 'b': {'c/d': 1}})

    def test_tilde_in_property_name(self):

        base = {'a': 0}
        head = {'~1': 1}

        base = jsonmerge.merge(base, head)

        self.assertEqual(base, {'a': 0, '~1': 1})

class TestGetSchema(unittest.TestCase):

    def test_default_overwrite(self):
        schema = {'description': 'test'}

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, {'description': 'test'})

    def test_default_object_merge_trivial(self):
        schema = {'type': 'object'}

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, {'type': 'object'})

    def test_default_object_merge(self):
        schema = {
            'properties': {
                'foo': {
                    'mergeStrategy': 'version',
                }
            }
        }

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2,
                         {
                             'properties': {
                                 'foo': {
                                     'type': 'array',
                                     'items': {
                                         'properties': {
                                             'value': {},
                                         }
                                     }
                                 }
                             }
                         })

    def test_overwrite(self):
        schema = {'mergeStrategy': 'overwrite'}

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, {})

    def test_append(self):
        schema = {'type': 'array',
                  'mergeStrategy': 'append'}

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, {'type': 'array'})

    def test_version(self):
        schema = {'mergeStrategy': 'version'}

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2,
                         {
                             'type': 'array',
                             'items': {
                                 'properties': {
                                     'value': {}
                                 }
                             }
                         })

    def test_version_ref_twice(self):
        schema = {
                'properties': {
                    'a': {
                        '$ref': '#/definitions/item'
                    },
                    'b': {
                        '$ref': '#/definitions/item'
                    },
                },
                'definitions': {
                    'item': {
                        'type': 'object',
                        'mergeStrategy': 'version'
                    }
                }
        }

        expected = {
                'properties': {
                    'a': {
                        '$ref': '#/definitions/item'
                    },
                    'b': {
                        '$ref': '#/definitions/item'
                    },
                },
                'definitions': {
                    'item': {
                        'type': 'array',
                        'items': {
                            'properties': {
                                'value': {
                                    'type': 'object',
                                }
                            }
                        }
                    }
                }
        }

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(expected, schema2)

    def test_version_meta(self):
        schema = {'type': 'object',
                  'mergeStrategy': 'version'}

        meta = {
            'properties': {
                'date': {},
                'version': {}
            }
        }

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema(meta)

        self.assertEqual(schema2,
                         {
                             'type': 'array',
                             'items': {
                                 'properties': {
                                     'value': {'type': 'object'},
                                     'date': {},
                                     'version': {}
                                 }
                             }
                         })

    def test_version_limit(self):
        schema = {'mergeStrategy': 'version',
                  'mergeOptions': {'limit': 5}}

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2,
                         {
                             'type': 'array',
                             'items': {
                                 'properties': {
                                     'value': {}
                                 }
                             },
                             'maxItems': 5
                         })

    def test_object_merge_simple(self):
        schema = {'mergeStrategy': 'objectMerge'}

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, {})

    def test_object_merge_nested(self):
        schema = {'mergeStrategy': 'objectMerge',
                  'properties': {
                      'foo': {'mergeStrategy': 'version'}
                  }}

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2,
                         {
                             'properties': {
                                 'foo': {
                                     'type': 'array',
                                     'items': {
                                         'properties': {
                                             'value': {}
                                         }
                                     }
                                 }
                             }
                         })

    def test_oneof(self):

        schema = {
            'mergeStrategy': 'objectMerge',
            'oneOf': [
                {'properties': {'a': {}}},
                {'properties': {'b': {}}}
            ]
        }

        merger = jsonmerge.Merger(schema)
        self.assertRaises(SchemaError, merger.get_schema)

    def test_external_refs(self):

        # We follow, but never resolve $refs in schemas. Internal or external.

        schema_1 = {
            'id': 'http://example.com/schema_1.json',
            '$ref': 'schema_2.json#/definitions/foo'
        }

        schema_2 = {
            'id': 'http://example.com/schema_2.json',
            'definitions': {
                'foo': {
                    'mergeStrategy': 'overwrite',
                    'properties': {
                        'bar': {
                            '$ref': '#/definitions/baz'
                        },
                        'b': {}
                    },
                },
                'baz': {
                    'mergeStrategy': 'append'
                }
            }
        }

        merger = jsonmerge.Merger(schema_1)
        merger.cache_schema(schema_2)

        mschema = merger.get_schema()

        d = {
            'id': 'http://example.com/schema_1.json',
            '$ref': 'schema_2.json#/definitions/foo'
        }

        self.assertEqual(d, mschema)

    def test_internal_refs(self):

        # We follow, but never resolve $refs in schemas. Internal or external.

        schema = {
            'id': 'http://example.com/schema_1.json',
            'mergeStrategy': 'overwrite',
            'properties': {
                'foo': {
                    '$ref': '#/definitions/bar'
                }
            },
            'definitions': {
                'bar': {
                    'properties': {
                        'baz': {}
                    }
                }
            }
        }

        expected = {
            'id': 'http://example.com/schema_1.json',
            'properties': {
                'foo': {
                    '$ref': '#/definitions/bar'
                }
            },
            'definitions': {
                'bar': {
                    'properties': {
                        'baz': {}
                    }
                }
            }
        }

        merger = jsonmerge.Merger(schema)

        mschema = merger.get_schema()

        self.assertEqual(expected, mschema)

    def test_reference_in_meta(self):

        schema = {'mergeStrategy': 'version'}

        meta_schema = {
            'id': 'http://example.com/schema_1.json',
            '$ref': 'schema_2.json#/definitions/meta'
        }

        schema_2 = {
            'id': 'http://example.com/schema_2.json',
            'definitions': {
                'meta': {
                    'properties': {
                        'foo': {
                            'type': 'string'
                        }
                    }
                }
            }
        }

        merger = jsonmerge.Merger(schema)
        merger.cache_schema(schema_2)

        mschema = merger.get_schema(meta=meta_schema)

        self.assertEqual(mschema,
                         {
                             'type': 'array',
                             'items': {
                                 'properties': {
                                     'value': {},
                                     'foo': {'type': 'string'}
                                 }
                             }
                         })

    def test_array_in_schema(self):

        schema = {
            'mergeStrategy': 'overwrite',
            'enum': [
                "foo",
                "bar",
            ]
        }

        expected = {
            'enum': [
                "foo",
                "bar",
            ]
        }

        merger = jsonmerge.Merger(schema)
        mschema = merger.get_schema()

        self.assertEqual(expected, mschema)

    def test_version_adds_array_type(self):
        schema = {
            "type": "object",
            "properties": {
                "buyer": {
                    "properties": {
                        "id": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "mergeStrategy": "version"
                                }
                            }
                        }
                    }
                }
            }
        }

        expected = {
            "type": "object",
            "properties": {
                "buyer": {
                    "properties": {
                        "id": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "array",
                                    "items": {
                                        "properties": {
                                            "value": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, expected)

    def test_merge_by_id(self):

        schema = {
            "mergeStrategy": "arrayMergeById",
            "items": {
                'type': 'object'
            }
        }

        expected = {
            "items": {
                'type': 'object'
            }
        }

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, expected)

    def test_merge_by_id_with_depth(self):

        schema = {
            "properties": {
                "test": {
                    "mergeStrategy": "arrayMergeById",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/refitem"
                    }
                }
            },
            "definitions": {
                "refitem": {
                    "type": "object",
                    "properties": {
                        "field1": {
                            "type": "string",
                            "mergeStrategy": "version"
                        }
                    }
                }
            }
        }

        expected = {
            "properties": {
                "test": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/refitem"
                    }
                }
            },
            "definitions": {
                "refitem": {
                    "type": "object",
                    "properties": {
                        "field1": {
                            "type": "array",
                            "items": {
                                "properties": {
                                    "value": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, expected)

    def test_merge_by_id_with_depth_twice(self):

        # Here were have a $ref that get_schema() should descend into twice.

        schema = {
            "properties": {
                "test": {
                    "mergeStrategy": "arrayMergeById",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/refitem"
                    }
                },
                "test2": {
                    "mergeStrategy": "arrayMergeById",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/refitem"
                    }
                }
            },
            "definitions": {
                "refitem": {
                    "type": "object",
                    "properties": {
                        "field1": {
                            "type": "string",
                            "mergeStrategy": "version"
                        }
                    }
                }
            }
        }

        expected = {
            "properties": {
                "test": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/refitem"
                    }
                },
                "test2": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/refitem"
                    }
                }
            },
            "definitions": {
                "refitem": {
                    "type": "object",
                    "properties": {
                        "field1": {
                            "type": "array",
                            "items": {
                                "properties": {
                                    "value": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        self.maxDiff = None

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, expected)

    def test_merge_by_id_with_depth_no_ref(self):
        schema = {
            "properties": {
                "test": {
                    "mergeStrategy": "arrayMergeById",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field1": {
                                "type": "string",
                                "mergeStrategy": "version"
                            }
                        }
                    }
                }
            }
        }

        expected = {
            "properties": {
                "test": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field1": {
                                "type": "array",
                                "items": {
                                    "properties": {
                                        "value": {
                                            "type": "string"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, expected)

    def test_merge_append_additional(self):

        schema = {'mergeStrategy': 'objectMerge',
                  'properties': {
                      'b': {'mergeStrategy': 'overwrite'}
                  },
                  'additionalProperties': {
                      'mergeStrategy': 'append'
                  }}

        expected = {'properties': {
                        'b': {},
                    },
                    'additionalProperties': {}
                }

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, expected)

    def test_oneof(self):

        schema = {
            'oneOf': [
                {
                    'type': 'array',
                    'mergeStrategy': 'append'
                },
                {
                    'type': 'object'
                }
            ]
        }

        expected = {
            'oneOf': [
                {
                    'type': 'array',
                },
                {
                    'type': 'object'
                }
            ]
        }

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, expected)

if __name__ == '__main__':
    unittest.main()

