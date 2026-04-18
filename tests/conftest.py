"""Pytest configuration and fixtures."""

import sys
import os
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

# Test environment variables
os.environ.setdefault("GROQ_API_KEY", "test-key-not-real")