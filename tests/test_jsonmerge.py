# vim:ts=4 sw=4 expandtab softtabstop=4
import unittest
import warnings

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

try:
    Draft6Validator = jsonschema.validators.Draft6Validator
except AttributeError:
    Draft6Validator = None

warnings.simplefilter("always")

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
        base = merger.merge(base, "a", merge_options={
                'version': {'metadata': {'uri': 'http://example.com/a'}}})
        base = merger.merge(base, "b", merge_options={
                'version': {'metadata': {'uri': 'http://example.com/b'}}})

        self.assertEqual(base, [
            {'value': "a",
             'uri': 'http://example.com/a'},
            {'value': "b",
             'uri': 'http://example.com/b'}])

    def test_version_meta_not_obj(self):

        schema = {'mergeStrategy': 'version'}
        merger = jsonmerge.Merger(schema)

        with self.assertRaises(SchemaError) as cm:
            merger.merge(None, "a", merge_options={'version': {'metadata': 'foo'}})

    def test_version_meta_deprecated(self):
        schema = {'mergeStrategy': 'version'}
        merger = jsonmerge.Merger(schema)

        with warnings.catch_warnings(record=True) as w:
            base = merger.merge(None, 'a', meta={'foo': 'bar'})

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))

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

    def test_version_base_not_a_list(self):

        schema = {'mergeStrategy': 'version'}

        base = "a"

        with self.assertRaises(BaseInstanceError) as cm:
            jsonmerge.merge(base, "b", schema)

    def test_version_base_not_a_list_of_objects(self):

        schema = {'mergeStrategy': 'version'}

        base = ["a"]

        with self.assertRaises(BaseInstanceError) as cm:
            jsonmerge.merge(base, "b", schema)

    def test_version_base_no_value_in_object(self):

        schema = {'mergeStrategy': 'version'}

        base = [{}]

        with self.assertRaises(BaseInstanceError) as cm:
            jsonmerge.merge(base, "b", schema)

    def test_version_base_empty_list(self):

        schema = {'mergeStrategy': 'version'}

        base = []
        base = jsonmerge.merge(base, "b", schema)

        self.assertEqual(base, [{'value': 'b'}])

    def test_append(self):
        schema = {'mergeStrategy': 'append'}

        base = None
        base = jsonmerge.merge(base, ["a"], schema)
        base = jsonmerge.merge(base, ["b"], schema)

        self.assertEqual(base, ["a", "b"])

    def test_append_type_error(self):

        schema = {'mergeStrategy': 'append'}

        base = None

        with self.assertRaises(HeadInstanceError) as cm:
            jsonmerge.merge(base, "a", schema)

        self.assertEqual(cm.exception.value.ref, "#")

    def test_append_type_error_base(self):

        schema = {'mergeStrategy': 'append'}

        base = "ab"

        with self.assertRaises(BaseInstanceError) as cm:
            jsonmerge.merge(base, ["a"], schema)

        self.assertEqual(cm.exception.value.ref, "#")

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
        with self.assertRaises(HeadInstanceError) as cm:
            jsonmerge.merge(base, "a", schema)

        self.assertEqual(cm.exception.value.ref, "#")

    def test_merge_type_error_base(self):

        schema = {'mergeStrategy': 'objectMerge'}

        base = "ab"
        with self.assertRaises(BaseInstanceError) as cm:
            jsonmerge.merge(base, {'foo': 1}, schema)

        self.assertEqual(cm.exception.value.ref, "#")

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
        base = merger.merge(base, OrderedDict([('c', "a"), ('a', "a")]))
        self.assertIsInstance(base, OrderedDict)
        self.assertEqual([k for k in base], ['c', 'a'])

        base = merger.merge(base, {'a': "b"})
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
        base = merger.merge(base, {'a': {'b': 'c'}, 'd': {'e': 'f'}})

        self.assertIsInstance(base, dict)
        self.assertIsInstance(base['a'], OrderedDict)
        self.assertIsInstance(base['d'], dict)

    def test_merge_objclass_bad_cls(self):
        schema = {'mergeStrategy': 'objectMerge', 'mergeOptions': { 'objClass': 'foo'}}

        merger = jsonmerge.Merger(schema)

        base = None
        with self.assertRaises(SchemaError) as cm:
            merger.merge(base, OrderedDict([('c', "a"), ('a', "a")]))

        self.assertEqual(cm.exception.value.ref, '#')

    def test_merge_objclass_menu(self):
        schema = {'mergeStrategy': 'objectMerge', 'mergeOptions': { 'objClass': 'foo'}}

        class MyDict(dict):
            pass

        objclass_menu = {'foo': MyDict}

        merger = jsonmerge.Merger(schema, objclass_menu=objclass_menu)

        base = None
        base = merger.merge(base, {'c': "a", 'a': "a"})

        self.assertTrue(isinstance(base, MyDict))

    def test_merge_objclass_def(self):
        schema = {'mergeStrategy': 'objectMerge'}

        merger = jsonmerge.Merger(schema, objclass_def='OrderedDict')

        base = None
        base = merger.merge(base, OrderedDict([('c', "a"), ('a', "a")]))
        self.assertIsInstance(base, OrderedDict)
        self.assertEqual([k for k in base], ['c', 'a'])

        base = merger.merge(base, {'a': "b"})
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

    def test_merge_additional_bool(self):

        schema = {'additionalProperties': True}

        base = {}
        head = {'a': 'a'}

        base = jsonmerge.merge(base, head, schema)

        self.assertEqual(base, {'a': 'a'})

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

    def test_internal_refs(self):

        schema = {
            'id': 'http://example.com/schema_1.json',
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

    def test_external_refs(self):

        schema_1 = {
            'id': 'http://example.com/schema_1.json',
            'properties': {
                'a': {'$ref': "schema_2.json#/definitions/a"},
            },
        }

        schema_2 = {
            'id': 'http://example.com/schema_2.json',
            'definitions': {
                "a": {
                    "properties": {
                        "b": {'mergeStrategy': 'version'},
                    }
                },
            }
        }

        merger = jsonmerge.Merger(schema_1)

        # merge() would otherwise make a HTTP request
        merger.cache_schema(schema_2)

        base = None
        base = merger.merge(base, {"a": {"b": "c"}})
        base = merger.merge(base, {"a": {"b": "d"}})

        self.assertEqual(base, {"a": {"b": [{"value": "c"}, {"value": "d"}]}})

    @unittest.skipIf(Draft6Validator is None, 'jsonschema too old')
    def test_external_refs_draft6(self):

        schema_1 = {
            '$id': 'http://example.com/schema_1.json',
            'properties': {
                'a': {'$ref': "schema_2.json#/definitions/a"},
            },
        }

        schema_2 = {
            '$id': 'http://example.com/schema_2.json',
            'definitions': {
                "a": {
                    "properties": {
                        "b": {'mergeStrategy': 'version'},
                    }
                },
            }
        }

        merger = jsonmerge.Merger(schema_1, validatorclass=Draft6Validator)

        # merge() would otherwise make a HTTP request
        merger.cache_schema(schema_2)

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

        with self.assertRaises(HeadInstanceError) as cm:
            merger.merge(base, {'b': 2})

        self.assertEqual(cm.exception.value.ref, '#')

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

    def test_oneof_overwrite_toplevel(self):
        schema = {
            'mergeStrategy': 'overwrite',
            'oneOf': [
                {
                    'type': 'array'
                },
                {
                    'type': 'string'
                },
            ]
        }

        merger = jsonmerge.Merger(schema)

        self.assertEqual(merger.merge([2, 3, 4], 'a'), 'a')
        self.assertEqual(merger.merge('a', [2, 3, 4]), [2, 3, 4])

    def test_oneof_multiple_validate(self):

        schema = {
            'oneOf': [
                {
                    'type': 'array',
                    'maxItems': 3,
                    'mergeStrategy': 'append'
                },
                {
                    'type': 'array',
                    'minItems': 2,
                    'mergeStrategy': 'overwrite'
                }
            ]
        }

        merger = jsonmerge.Merger(schema)

        base = [1]
        base = merger.merge(base, [2])

        self.assertEqual(base, [1, 2])

        base = [1, 2]

        with self.assertRaises(HeadInstanceError) as cm:
            base = merger.merge(base, [3, 4])

    def test_anyof(self):
        schema = {
            'anyOf': [
                {
                    'type': 'array'
                },
                {
                    'type': 'string'
                },
            ]
        }

        merger = jsonmerge.Merger(schema)

        with self.assertRaises(SchemaError) as cm:
                merger.merge([2, 3, 4], 'a')

        self.assertEqual(cm.exception.value.ref, '#')

    def test_anyof_overwrite_toplevel(self):
        schema = {
            'mergeStrategy': 'overwrite',
            'anyOf': [
                {
                    'type': 'array'
                },
                {
                    'type': 'string'
                },
            ]
        }

        merger = jsonmerge.Merger(schema)

        self.assertEqual(merger.merge([2, 3, 4], 'a'), 'a')
        self.assertEqual(merger.merge('a', [2, 3, 4]), [2, 3, 4])

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

    def test_merge_by_id_complex_id(self):
        schema = {
            "mergeStrategy": "arrayMergeById",
        }

        a = [
                {"id": ["A", {"B": "C"} ], "field": 1},
                {"id": ["A", {"B": "D"} ], "field": 2},
                {"id": ["A", {"B": "E"} ], "field": 3},
        ]

        b = [
                {"id": ["A", {"B": "D"} ], "field": 4},
                {"id": ["E", {"B": "C"} ], "field": 5},
        ]

        merger = jsonmerge.Merger(schema)

        c = merger.merge(a, b)

        expected = [
                {"id": ["A", {"B": "C"} ], "field": 1},
                {"id": ["A", {"B": "D"} ], "field": 4},
                {"id": ["A", {"B": "E"} ], "field": 3},
                {"id": ["E", {"B": "C"} ], "field": 5},
        ]

        self.assertEqual(expected, c)

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

        with self.assertRaises(SchemaError) as cm:
            merger.merge(base, head)

        self.assertEqual(cm.exception.value.ref, '#/items')

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
        with self.assertRaises(HeadInstanceError) as cm:
            merger.merge(base, head)

        self.assertEqual(cm.exception.value.ref, '#')

    def test_merge_by_id_bad_base_type(self):
        schema = {
            'mergeStrategy': 'arrayMergeById'
        }

        head = []
        base = {'foo': 'bar'}

        merger = jsonmerge.Merger(schema)
        with self.assertRaises(BaseInstanceError) as cm:
            merger.merge(base, head)

        self.assertEqual(cm.exception.value.ref, '#')

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

        with self.assertRaises(BaseInstanceError) as cm:
            merger.merge(base, head)

        self.assertEqual(cm.exception.value.ref, '#/1')

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

        with self.assertRaises(HeadInstanceError) as cm:
            merger.merge(base, head)

        self.assertEqual(cm.exception.value.ref, '#/1')

    def test_merge_by_id_order_issue_31_1(self):

        # There was an issue with arrayMergeById where head value would be
        # merged with the last item in the base list, not the matching item.
        # The result was then assigned to the matching item.
        #
        # If the last item in the base list was just created in the same
        # arrayMergeById (i.e. by another item in the head list), then merge
        # would fail with "Unresolvable JSON pointer".
        #
        # https://github.com/avian2/jsonmerge/pull/31
        schema = {
            "mergeStrategy": "arrayMergeById",
        }

        base = [
            {'id': 'a', 'val': {'a': 1}},
            {'id': 'b', 'val': {'b': 2}},
        ]

        head = [
            {'id': 'a', 'val': {'c': 3}}
        ]

        expected = [
            # bug would produce {'b': 2, 'c': 3} here
            {'id': 'a', 'val': {'a': 1, 'c': 3}},
            {'id': 'b', 'val': {'b': 2}},
        ]

        merger = jsonmerge.Merger(schema)
        base = merger.merge(base, head)
        self.assertEqual(base, expected)

    def test_merge_by_id_order_issue_31_2(self):

        schema = {
            "mergeStrategy": "arrayMergeById",
        }

        base = [
            {'id': 'a', 'val': {'a': 1}},
            {'id': 'b', 'val': {'b': 2}},
        ]

        head = [
            # this caused "Unresolvable JSON pointer"
            {'id': 'c', 'val': {'c': 3}},
            {'id': 'a', 'val': {'c': 3}}
        ]

        expected = [
            {'id': 'a', 'val': {'a': 1, 'c': 3}},
            {'id': 'b', 'val': {'b': 2}},
            {'id': 'c', 'val': {'c': 3}}
        ]

        merger = jsonmerge.Merger(schema)
        base = merger.merge(base, head)
        self.assertEqual(base, expected)

    def test_merge_by_id_subclass_get_key(self):

        class MyArrayMergeById(jsonmerge.strategies.ArrayMergeById):
            def get_key(self, walk, item, idRef):
                return item.val[-1]

        schema = {'mergeStrategy': 'myArrayMergeById'}

        merger = jsonmerge.Merger(schema=schema,
                                  strategies={'myArrayMergeById': MyArrayMergeById()})

        base = [
                [ 'a', 'b', 'id1' ],
                [ 'c', 'id2' ],
        ]

        head = [
                [ 'e', 'f', 'g', 'id3' ],
                [ 'd', 'id1' ],
        ]

        expected = [
                [ 'd', 'id1' ],
                [ 'c', 'id2' ],
                [ 'e', 'f', 'g', 'id3' ],
        ]

        base = merger.merge(base, head)

        self.assertEqual(base, expected)

    def test_merge_by_id_multiple_ids(self):

        schema = {
                'mergeStrategy': 'arrayMergeById',
                'mergeOptions': { 'idRef': ['/a', '/b'] }
        }

        base = [
                {
                    'a': 1,
                    'b': 2
                },
                {
                    'a': 1,
                    'b': 1,
                }
        ]

        head = [
                {
                    'a': 1,
                    'b': 1,
                    'c': 2,
                },
                {
                    # incomplete key, ignored
                    'b': 1,
                },
                {
                    'a': 2,
                    'b': 2,
                    'c': 3,
                }
        ]

        expected = [
                {
                    'a': 1,
                    'b': 2
                },
                {
                    'a': 1,
                    'b': 1,
                    'c': 2,
                },
                {
                    'a': 2,
                    'b': 2,
                    'c': 3,
                }
        ]

        merger = jsonmerge.Merger(schema)
        base = merger.merge(base, head)
        self.assertEqual(base, expected)

    def test_merge_by_id_multiple_ids_ignore(self):

        schema = {
                'mergeStrategy': 'arrayMergeById',
                'mergeOptions': {
                    'idRef': ['/a', '/b'],
                    'ignoreId': [1, 2],
                }
        }

        base = [
                {
                    'a': 1,
                    'b': 1,
                }
        ]

        head = [
                {
                    # ignoreId matches
                    'a': 1,
                    'b': 2,
                    'c': 2,
                },
                {
                    'a': 2,
                    'b': 2,
                    'c': 3,
                }
        ]

        expected = [
                {
                    'a': 1,
                    'b': 1
                },
                {
                    'a': 2,
                    'b': 2,
                    'c': 3,
                }
        ]

        merger = jsonmerge.Merger(schema)
        base = merger.merge(base, head)
        self.assertEqual(base, expected)

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

    def test_discard(self):

        schema = {'mergeStrategy': 'discard'}

        base = "a"
        base = jsonmerge.merge(base, "b", schema)

        self.assertEqual(base, "a")

    def test_discard_objectmerge_null(self):

        schema = {
                'properties': {
                    'a': {
                        'mergeStrategy': 'discard'
                    }
                } }

        base = {}
        head = {'a': 1}

        base = jsonmerge.merge(base, head, schema)
        self.assertEqual(base, {})

    def test_discard_arraymergebyid(self):

        schema = {
                'mergeStrategy': 'arrayMergeById',
                'items': {
                    'mergeStrategy': 'discard'
                } }

        base = [ {'id': 1, 'val': 1} ]
        head = [ {'id': 1, 'val': 2} ]

        base = jsonmerge.merge(base, head, schema)
        self.assertEqual(base, [{'id': 1, 'val': 1}])

    def test_discard_arraymergebyid_null(self):

        schema = {
                'mergeStrategy': 'arrayMergeById',
                'items': {
                    'mergeStrategy': 'discard'
                } }

        base = [ ]
        head = [ {'id': 1, 'val': 1} ]

        base = jsonmerge.merge(base, head, schema)
        self.assertEqual(base, [])

    def test_discard_null_keep(self):

        schema = {
                'properties': {
                    'a': {
                        'mergeStrategy': 'discard',
                        'mergeOptions': {
                            'keepIfUndef': True
                        }
                    }
                } }

        base = {}
        head = {'a': 1}

        base = jsonmerge.merge(base, head, schema)
        self.assertEqual(base, {'a': 1})

        head = {'a': 2}

        base = jsonmerge.merge(base, head, schema)
        self.assertEqual(base, {'a': 1})

    def test_bad_strategy(self):

        schema = {
                'properties': {
                    'a': {
                        'mergeStrategy': 'invalidStrategy'
                    } } }

        base = {'a': 1 }
        head = {'a': 2 }

        with self.assertRaises(SchemaError) as cm:
            jsonmerge.merge(base, head, schema)

        self.assertEqual(cm.exception.value.ref, '#/properties/a')

    def test_nan(self):
        # float('nan') == float('nan') evaluates to false.
        #
        # https://github.com/avian2/jsonmerge/issues/39
        base = {
            "foo": 1,
            "bar": float('nan')
        }

        head = {
            "foo": 1,
            "bar": float('nan')
        }

        base = jsonmerge.merge(base, head)

    def test_merge_by_index(self):

        schema = {
                'mergeStrategy': 'arrayMergeByIndex'
        }

        base = [ {'a': 0 }, {'b': 1} ]
        head = [ {'c': 2 }, {'d': 3} ]

        result = jsonmerge.merge(base, head, schema)

        self.assertEqual(result, [ {'a': 0, 'c': 2}, {'b': 1, 'd': 3} ])

    def test_merge_by_index_empty(self):

        schema = {
                'mergeStrategy': 'arrayMergeByIndex'
        }

        base = [ ]
        head = [ {'c': 2 }, {'d': 3} ]

        result = jsonmerge.merge(base, head, schema)

        self.assertEqual(result, [ {'c': 2}, {'d': 3} ])


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
        schema2 = merger.get_schema(merge_options={
            'version': {'metadataSchema': meta}})

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

    def test_version_meta_deprecated(self):
        schema = {'mergeStrategy': 'version'}
        merger = jsonmerge.Merger(schema)

        with warnings.catch_warnings(record=True) as w:
            merger.get_schema(meta={'foo': 'bar'})

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))

    def test_version_meta_in_schema(self):
        schema = {
                'type': 'object',
                'mergeStrategy': 'version',
                'mergeOptions': {
                    'metadataSchema': {
                        'properties': {
                            'date': {},
                            'version': {},
                        },
                    },
                },
        }

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

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

    def test_anyof_descend(self):
        # We don't support descending through 'anyOf', since each branch could
        # have its own rules for merging. How could we then decide which rule
        # to follow?

        schema = {
            'anyOf': [
                {'properties': {'a': {}}},
                {'properties': {'b': {}}}
            ]
        }

        merger = jsonmerge.Merger(schema)
        with self.assertRaises(SchemaError) as cm:
            merger.get_schema()

        self.assertEqual(cm.exception.value.ref, '#')

    def test_anyof_dont_descend(self):
        # However, 'anyOf' should be fine if we don't descend through it (e.g.
        # if it's after a 'overwrite' strategy for instance.

        schema = {
            'properties': {
                'a': {
                    'mergeStrategy': 'overwrite',
                    'properties': {
                        'b': {
                            'anyOf': [
                                {'properties': {'c': {}}},
                                {'properties': {'d': {}}},
                            ]
                        }
                    }
                }
            }
        }

        expected = {
            'properties': {
                'a': {
                    'properties': {
                        'b': {
                            'anyOf': [
                                {'properties': {'c': {}}},
                                {'properties': {'d': {}}},
                            ]
                        }
                    }
                }
            }
        }

        merger = jsonmerge.Merger(schema)
        mschema = merger.get_schema()
        self.assertEqual(expected, mschema)

    def test_external_refs(self):

        schema_1 = {
            'id': 'http://example.com/schema_1.json',
            '$ref': 'schema_2.json#/definitions/foo'
        }

        # get_schema() shouldn't do external HTTP requests for schemas.
        merger = jsonmerge.Merger(schema_1)
        mschema = merger.get_schema()

        d = {
            'id': 'http://example.com/schema_1.json',
            '$ref': 'schema_2.json#/definitions/foo'
        }

        self.assertEqual(d, mschema)

    def test_internal_refs(self):

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

    def test_ref_to_non_object_is_an_error(self):

        schema = {
                'properties': {
                    'foo': {
                        '$ref': '#/definitions/bar'
                    }
                },
                'definitions': {
                    'bar': []
                }
        }

        merger = jsonmerge.Merger(schema)

        with self.assertRaises(SchemaError) as cm:
            merger.get_schema()

        self.assertEqual(cm.exception.value.ref, '#/properties/foo')

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
                        },
                        'bar': {
                            'enum': [ 'a', 'b' ]
                        }
                    }
                }
            }
        }

        merger = jsonmerge.Merger(schema)
        merger.cache_schema(schema_2)

        mschema = merger.get_schema(merge_options={
            'version': {'metadataSchema': meta_schema}})

        self.assertEqual(mschema,
                         {
                             'type': 'array',
                             'items': {
                                 'properties': {
                                     'value': {},
                                     'foo': {'type': 'string'},
                                     'bar': {'enum': ['a', 'b'] },
                                 }
                             }
                         })

    def test_local_reference_in_meta(self):

        schema = {
                'properties': {
                    'content': {
                        'mergeStrategy': 'version',
                        'mergeOptions': {
                            'metadataSchema': {
                                '$ref': '#/definitions/metadata',
                            },
                        },
                    },
                },
                'definitions': {
                    'metadata': {
                        'properties': {
                            'revision': {
                                'type': 'number',
                            },
                        },
                    },
                },
        }

        merger = jsonmerge.Merger(schema)
        mschema = merger.get_schema()

        self.assertEqual(mschema, {
                            'properties': {
                                'content': {
                                    'type': 'array',
                                    'items': {
                                        'properties': {
                                            'value': {},
                                            'revision': {
                                                'type': 'number',
                                            },
                                        },
                                    },
                                },
                            },
                            'definitions': {
                                'metadata': {
                                    'properties': {
                                        'revision': {
                                            'type': 'number',
                                        },
                                    },
                                },
                            },
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

    def test_merge_additional_bool(self):

        schema = {'additionalProperties': True}

        base = {}
        head = {'a': 'a'}

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, schema)

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

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, schema)

    def test_oneof_toplevel(self):

        schema = {
            "mergeStrategy": "version",
            "oneOf": [
                {"type": "string", "pattern": "^!?(?:[0-9]{1,3}\\.){3}[0-9]{1,3}(?:\\/[0-9]{1,2})?$"},
                {"type": "string", "format": "hostname"}
            ]
        }

        expected = {
            "type": "array",
            "items": {
                "properties": {
                    "value": {
                        "oneOf": [
                            {"type": "string", "pattern": "^!?(?:[0-9]{1,3}\\.){3}[0-9]{1,3}(?:\\/[0-9]{1,2})?$"},
                            {"type": "string", "format": "hostname"}
                        ]
                    }
                }
            }
        }

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, expected)

    def test_anyof_toplevel(self):

        schema = {
            "mergeStrategy": "version",
            "anyOf": [
                {"type": "string", "pattern": "^!?(?:[0-9]{1,3}\\.){3}[0-9]{1,3}(?:\\/[0-9]{1,2})?$"},
                {"type": "string", "format": "hostname"}
            ]
        }

        expected = {
            "type": "array",
            "items": {
                "properties": {
                    "value": {
                        "anyOf": [
                            {"type": "string", "pattern": "^!?(?:[0-9]{1,3}\\.){3}[0-9]{1,3}(?:\\/[0-9]{1,2})?$"},
                            {"type": "string", "format": "hostname"}
                        ]
                    }
                }
            }
        }

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        self.assertEqual(schema2, expected)

    def test_discard(self):

        schema = {  'type': 'string',
                    'mergeStrategy': 'discard' }

        merger = jsonmerge.Merger(schema)
        schema2 = merger.get_schema()

        expected = { 'type': 'string' }

        self.assertEqual(schema2, expected)

    def test_bad_strategy(self):

        schema = {
                'properties': {
                    'a': {
                        'mergeStrategy': 'invalidStrategy'
                    } } }

        merger = jsonmerge.Merger(schema)

        with self.assertRaises(SchemaError) as cm:
            merger.get_schema()

        self.assertEqual(cm.exception.value.ref, '#/properties/a')

    def test_merge_by_index(self):

        schema = {
                'type': 'array',
                'mergeStrategy': 'arrayMergeByIndex'
        }

        merger = jsonmerge.Merger(schema)
        result = merger.get_schema()

        self.assertEqual(result, {'type': 'array'})

    def test_merge_by_index_name_in_exception(self):
        schema = {
            'properties': {
                'a': {
                    'mergeStrategy': 'arrayMergeByIndex'
                }
            }
        }

        head = {'a': {}}
        base = {'a': []}

        merger = jsonmerge.Merger(schema)
        with self.assertRaises(HeadInstanceError) as cm:
            merger.merge(base, head)

        self.assertIn('arrayMergeByIndex', str(cm.exception))

class TestExceptions(unittest.TestCase):
    def test_str_with_ref(self):
        e = SchemaError("Test error", JSONValue({}, '#'))

        self.assertEqual(str(e), 'Test error: #')

    def test_str(self):
        e = SchemaError("Test error")

        self.assertEqual(str(e), 'Test error')

    def test_str_with_name(self):
        e = SchemaError("Test error", JSONValue({}, '#'), 'test')

        self.assertEqual(str(e), "'test' merge strategy: Test error: #")

if __name__ == '__main__':
    unittest.main()
