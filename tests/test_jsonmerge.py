import unittest
import jsonmerge
import datadiff

class TestJsonMerge(unittest.TestCase):

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

    def test_version_last(self):

        schema = {'mergeStrategy': 'versionLast'}

        base = None
        base = jsonmerge.merge(base, "a", schema)
        base = jsonmerge.merge(base, "b", schema)

        self.assertEqual(base, {'value': "b"})

    def test_append(self):

        schema = {'mergeStrategy': 'append'}

        base = None
        base = jsonmerge.merge(base, ["a"], schema)
        base = jsonmerge.merge(base, ["b"], schema)

        self.assertEqual(base, ["a", "b"])

    def test_merge_default(self):

        schema = {}

        base = None
        base = jsonmerge.merge(base, {'a': "a"}, schema)
        base = jsonmerge.merge(base, {'b': "b"}, schema)

        self.assertEqual(base, {'a': "a",  'b': "b"})


    def test_merge_trivial(self):

        schema = {'mergeStrategy': 'objectMerge'}

        base = None
        base = jsonmerge.merge(base, {'a': "a"}, schema)
        base = jsonmerge.merge(base, {'b': "b"}, schema)

        self.assertEqual(base, {'a': "a",  'b': "b"})

    def test_merge_overwrite(self):

        schema = {'mergeStrategy': 'objectMerge'}

        base = None
        base = jsonmerge.merge(base, {'a': "a"}, schema)
        base = jsonmerge.merge(base, {'a': "b"}, schema)

        self.assertEqual(base, {'a': "b"})

    def test_merge_append(self):

        schema =    {
                        'mergeStrategy': 'objectMerge',
                        'properties': {
                            'a': {'mergeStrategy': 'append' }
                        }
                    }

        base = None
        base = jsonmerge.merge(base, {'a': ["a"]}, schema)
        base = jsonmerge.merge(base, {'a': ["b"], 'b': 'c'}, schema)

        self.assertEqual(base, {'a': ["a", "b"], 'b': 'c'})

    def test_example(self):

        head1 =     {
                        'buyer': {
                            'id': {
                                'name': "Test old",
                            },
                            'uri': 'Test uri old',
                        }
                    }

        head2 =     {
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
                                    {'value': "Test old" },
                                    {'value': "Test new" },
                                ]
                            },
                            'uri': 'Test uri new',
                        },

                        'award': "Award"
                    }

        schema =    {
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
