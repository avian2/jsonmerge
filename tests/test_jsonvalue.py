# vim:ts=4 sw=4 expandtab softtabstop=4
import unittest
from jsonmerge.jsonvalue import JSONValue

class TestJSONValue(unittest.TestCase):

    def test_get_attr(self):
        v = JSONValue({'a': 'b'})

        va = v['a']
        self.assertEqual('b', va.val)
        self.assertEqual('#/a', va.ref)

    def test_get_default(self):
        v = JSONValue({})

        va = v.get('a')
        self.assertTrue(va.is_undef())

    def test_get(self):
        v = JSONValue({'a': 'b'})

        va = v.get('a')
        self.assertTrue('b', va.val)
        self.assertEqual('#/a', va.ref)
