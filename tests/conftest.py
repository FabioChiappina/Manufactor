"""
Shared pytest fixtures for the Manufactor test suite.
"""

import pytest


@pytest.fixture
def mock_common_tokens():
    """Return a list of common token names mirroring config/common_tokens.json."""
    return ["Treasure", "Clue", "Food", "Blood", "Map", "Powerstone", "Junk"]
