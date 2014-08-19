#!/usr/bin/python

from distutils.core import Command, setup
from sys import version_info
import unittest

UNITTESTS = [
        "test_jsonmerge",
        "test_readme",
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
    version='1.0.0',
    description='Merge a series of JSON documents.',
    license='MIT',
    long_description=open("README.rst").read(),
    author='Tomaz Solc',
    author_email='tomaz.solc@tablix.org',

    packages = [ 'jsonmerge' ],

    requires = [ 'jsonschema' ],

    cmdclass = { 'test': TestCommand },
)
