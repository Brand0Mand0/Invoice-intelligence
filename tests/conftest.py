"""
Pytest configuration and fixtures.

Configures the test environment and provides common fixtures.
"""

import sys
import os
import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
