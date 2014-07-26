#!/usr/bin/python

from distutils.core import Command, setup
from sys import version_info
import unittest

UNITTESTS = [
		"test_jsonmerge",
	]

class TestCommand(Command):
	user_options = [ ]

	def initialize_options(self):
		pass

	def finalize_options(self):
		pass

	def run(self):
		suite = unittest.TestSuite()

		suite.addTests(
			unittest.defaultTestLoader.loadTestsFromNames(
				"tests." + test for test in UNITTESTS) )

		result = unittest.TextTestRunner(verbosity=2).run(suite)

setup(name='jsonmerge',
      version='1.0',
      description='',
      license='GPL',
      long_description='',
      author='Tomaz Solc',
      author_email='tomaz.solc@tablix.org',

      packages = [ 'jsonmerge' ],

      cmdclass = { 'test': TestCommand },
)
