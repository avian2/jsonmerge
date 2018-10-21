# vim:ts=4 sw=4 expandtab softtabstop=4
import unittest
from jsonmerge.jsonvalue import JSONValue

class TestJSONValue(unittest.TestCase):

    def test_get_attr(self):
        v = JSONValue({'a': 'b'})

        va = v['a']
        self.assertEqual('b', va.val)
        self.assertEqual('#/a', va.ref)

    def test_get_attr_nonascii(self):
        v = JSONValue({u'\u20ac': 'b'})

        va = v[u'\u20ac']
        self.assertEqual('b', va.val)
        self.assertEqual(u'#/\u20ac', va.ref)

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

    def test_undef(self):
        v = JSONValue(undef=True)
        self.assertTrue(v.is_undef())

    def test_dict_set_attr(self):
        v = JSONValue({})

        v['a'] = JSONValue('b')

        self.assertEqual({'a': 'b'}, v.val)

    def test_dict_set_attr_undef(self):
        v = JSONValue({})

        v['a'] = JSONValue(undef=True)

        self.assertEqual({}, v.val)

    def test_dict_set_attr_undef_exists(self):
        v = JSONValue({'a': 'b'})

        v['a'] = JSONValue(undef=True)

        self.assertEqual({}, v.val)

    def test_list_set_attr(self):
        v = JSONValue([1])

        v[0] = JSONValue(2)

        self.assertEqual([2], v.val)

    def test_list_set_attr_undef_exists(self):
        v = JSONValue([1])

        # Setting a list element to undef does not make sense.
        with self.assertRaises(ValueError) as cm:
            v[0] = JSONValue(undef=True)

    def test_list_set_attr_undef(self):
        v = JSONValue([])

        with self.assertRaises(ValueError) as cm:
            v[0] = JSONValue(undef=True)

    def test_append_undef(self):
        v = JSONValue([])

        v.append(JSONValue(undef=True))

        self.assertEqual([], v.val)
