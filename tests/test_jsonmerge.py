import unittest
import jsonmerge
import datadiff

class TestJsonMerge(unittest.TestCase):

	def test_string(self):

		base = "a"
		head = "b"

		schema = {}

		base = jsonmerge.merge(base, head, schema)

		self.assertEqual(base, "b")
