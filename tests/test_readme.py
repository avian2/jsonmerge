import doctest

def additional_tests():
	return doctest.DocFileSuite("../README.rst", optionflags=doctest.IGNORE_EXCEPTION_DETAIL)
