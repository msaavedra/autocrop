#!/usr/bin/env python2

import os
import unittest
from doctest import DocTestSuite, NORMALIZE_WHITESPACE
from types import ModuleType

import autocrop

suite = unittest.TestSuite()

# Build and add tests from docstrings with doctest.
# Re-enable this when doctests are available.
#suite.addTest(DocTestSuite(autocrop))
#for obj in vars(autoscrop).values():
#    if isinstance(obj, ModuleType):
#        suite.addTest(DocTestSuite(obj))

# Add the test subpackages.
files = os.listdir(os.path.split(os.path.abspath(__file__))[0])
tests = [n[:-3] for n in files if n.startswith('test_') and n.endswith('.py')]
suite.addTest(unittest.defaultTestLoader.loadTestsFromNames(tests))

# Run everything.
unittest.TextTestRunner(verbosity=2).run(suite)

