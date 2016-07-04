# vim:ts=4 sw=4 expandtab softtabstop=4
import unittest
from jsonmerge.jsonvalue import JSONValue

class TestJSONValue(unittest.TestCase):

    def test_get_attr(self):
        v = JSONValue({'a': 'b'})

        va = v['a']
        self.assertEqual('b', va.val)
        self.assertEqual('#/a', va.ref)

    def test_get_attr_escape_slash(self):
        v = JSONValue({'a/b': 'c'})

        va = v['a/b']
        self.assertEqual('c', va.val)
        self.assertEqual('#/a~1b', va.ref)

    def test_get_attr_escape_tilde(self):
        v = JSONValue({'~0': 'a'})

        va = v['~0']
        self.assertEqual('a', va.val)
        self.assertEqual('#/~00', va.ref)

    def test_get_default(self):
        v = JSONValue({})

        va = v.get('a')
        self.assertTrue(va.is_undef())

    def test_get(self):
        v = JSONValue({'a': 'b'})

        va = v.get('a')
        self.assertTrue('b', va.val)
        self.assertEqual('#/a', va.ref)
