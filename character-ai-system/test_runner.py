"""
Simple test runner for Character AI System
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.test_character_ai import run_tests

if __name__ == "__main__":
    print("Character AI System Test Suite")
    print("=" * 50)
    success = run_tests()
    print("=" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed.")
    sys.exit(0 if success else 1)