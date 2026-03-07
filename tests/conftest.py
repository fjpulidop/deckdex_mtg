"""Shared test infrastructure for DeckDex MTG.

Provides:
- make_test_client(): helper for unittest.TestCase-based tests
- SAMPLE_CARDS: canonical sample data usable across test files
- Pytest fixtures (client, sample_cards): for new pytest-style tests
"""

import copy

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app

# ---------------------------------------------------------------------------
# Helper functions (usable from unittest.TestCase tests via import)
# ---------------------------------------------------------------------------


def make_test_client(user_id: int = 1) -> TestClient:
    """Return a TestClient with auth dependency overridden to a test user."""
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    return TestClient(app)


# ---------------------------------------------------------------------------
# Shared sample data
# ---------------------------------------------------------------------------

SAMPLE_CARDS = [
    {
        "name": "Lightning Bolt",
        "rarity": "common",
        "type": "Instant",
        "set_name": "M10",
        "price": "0.5",
        "color_identity": "R",
    },
    {
        "name": "Black Lotus",
        "rarity": "mythic rare",
        "type": "Artifact",
        "set_name": "LEA",
        "price": "25000",
        "color_identity": "",
    },
    {
        "name": "Counterspell",
        "rarity": "common",
        "type": "Instant",
        "set_name": "M10",
        "price": "1.2",
        "color_identity": "U",
    },
]


# ---------------------------------------------------------------------------
# Pytest fixtures (for new pytest-style tests)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def client():
    """Configured TestClient with auth override."""
    app.dependency_overrides[get_current_user_id] = lambda: 1
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
def sample_cards():
    """Fresh copy of sample cards — safe to mutate in tests."""
    return copy.deepcopy(SAMPLE_CARDS)
