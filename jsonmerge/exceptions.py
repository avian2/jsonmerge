class JSONMergeError(Exception):
	def __init__(self, message, value=None):
		self.value = value
		self.message = message

class BaseInstanceError(JSONMergeError): pass
class HeadInstanceError(JSONMergeError): pass
class SchemaError(JSONMergeError): pass
