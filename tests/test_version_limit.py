import copy
import unittest

import jsonschema

from jsonmerge import Merger


class TestVersionLimit(unittest.TestCase):
    def merger(self, limit):
        return Merger({'mergeStrategy': 'version',
                       'mergeOptions': {'limit': limit}})

    def assert_valid(self, merger, result, merge_options=None):
        jsonschema.validate(result, merger.get_schema(
            merge_options=merge_options))

    def test_zero_limit_with_undefined_base(self):
        merger = self.merger(0)
        result = merger.merge(None, 'new')
        self.assertEqual(result, [])
        self.assert_valid(merger, result)

    def test_zero_limit_with_existing_history(self):
        merger = self.merger(0)
        base = [{'value': 'old'}]
        result = merger.merge(base, 'new')
        self.assertEqual(result, [])
        self.assertEqual(base, [{'value': 'old'}])
        self.assert_valid(merger, result)

    def test_zero_limit_with_duplicate_head(self):
        merger = self.merger(0)
        result = merger.merge([{'value': 'same'}], 'same')
        self.assertEqual(result, [])
        self.assert_valid(merger, result)

    def test_zero_limit_over_repeated_merges(self):
        merger = self.merger(0)
        result = None
        for head in ['first', 'first', 'second']:
            result = merger.merge(result, head)
            self.assertEqual(result, [])
            self.assert_valid(merger, result)

    def test_positive_limit_with_duplicate_head(self):
        merger = self.merger(1)
        base = [{'value': 'old'}, {'value': 'same', 'revision': 2}]
        saved = copy.deepcopy(base)
        result = merger.merge(base, 'same')
        self.assertEqual(result, [{'value': 'same', 'revision': 2}])
        self.assertEqual(base, saved)
        self.assert_valid(merger, result)

    def test_runtime_limit_with_duplicate_head(self):
        merger = Merger({'mergeStrategy': 'version'})
        options = {'version': {'limit': 1}}
        result = merger.merge([{'value': 'old'}, {'value': 'same'}],
                              'same', merge_options=options)
        self.assertEqual(result, [{'value': 'same'}])
        self.assert_valid(merger, result, options)

    def test_schema_zero_limit_overrides_runtime_limit(self):
        merger = self.merger(0)
        options = {'version': {'limit': 2}}
        result = merger.merge(None, 'new', merge_options=options)
        self.assertEqual(result, [])
        self.assert_valid(merger, result, options)

    def test_nested_zero_limit(self):
        merger = Merger({'properties': {'history': {
            'mergeStrategy': 'version', 'mergeOptions': {'limit': 0}}}})
        result = merger.merge({'other': 1}, {'history': 'new'})
        self.assertEqual(result, {'other': 1, 'history': []})
        self.assert_valid(merger, result)

    def test_positive_limit_keeps_latest_appended_version(self):
        merger = self.merger(1)
        result = merger.merge([{'value': 'old'}], 'new')
        self.assertEqual(result, [{'value': 'new'}])
        self.assert_valid(merger, result)

    def test_zero_limit_with_duplicate_recording_enabled(self):
        merger = Merger({'mergeStrategy': 'version', 'mergeOptions': {
            'limit': 0, 'ignoreDups': False}})
        result = merger.merge([{'value': 'same'}], 'same')
        self.assertEqual(result, [])
        self.assert_valid(merger, result)

    def test_unlimited_history_keeps_existing_duplicate_behavior(self):
        merger = Merger({'mergeStrategy': 'version'})
        base = [{'value': 'old'}, {'value': 'same'}]
        self.assertEqual(merger.merge(base, 'same'), base)
        self.assertEqual(merger.merge(base, 'new'),
                         base + [{'value': 'new'}])


if __name__ == '__main__':
    unittest.main()
