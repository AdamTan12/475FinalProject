"""
Test suite driver — discovers and runs all tests in the tests/ directory.
Run from project root: python tests/test_runner.py
"""
import unittest
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

loader = unittest.TestLoader()
suite = loader.discover(start_dir=os.path.dirname(os.path.abspath(__file__)), pattern="test_*.py")

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

sys.exit(0 if result.wasSuccessful() else 1)
