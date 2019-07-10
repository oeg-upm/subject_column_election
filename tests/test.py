from __future__ import print_function
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# added this to import app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elect_tests import ElectTest
import unittest

combine_cases = unittest.TestLoader().loadTestsFromTestCase(ElectTest)
suite = unittest.TestSuite([combine_cases])
result = unittest.TextTestRunner().run(suite)
sys.exit(not result.wasSuccessful())
