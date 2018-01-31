class JSONMergeError(Exception):
	def __init__(self, message, value=None):
		self.message = message
		self.value = value

	def __str__(self):
		try:
			ref = self.value.ref
		except:
			ref = None

		if ref is not None:
			return "%s: %s" % (self.message, ref)
		else:
			return self.message

class BaseInstanceError(JSONMergeError): pass
class HeadInstanceError(JSONMergeError): pass
class SchemaError(JSONMergeError): pass
