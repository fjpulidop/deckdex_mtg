"""Unit tests for deckdex.variant_utils.derive_variant_label.

Pure-function tests — no mocking required.
All seven derivation branches are covered.
"""

import pytest

from deckdex.variant_utils import derive_variant_label


# ---------------------------------------------------------------------------
# Branch 1: Serialized (promo_types contains 'serialized')
# ---------------------------------------------------------------------------


def test_serialized_nonfoil():
    assert derive_variant_label("nonfoil", "serialized", None, None) == "Serialized"


def test_serialized_foil():
    assert derive_variant_label("foil", "serialized", None, None) == "Serialized Foil"


def test_serialized_case_insensitive():
    """promo_types values are comma-separated lowercase after joining."""
    assert derive_variant_label("nonfoil", "SERIALIZED", None, None) == "Serialized"


# ---------------------------------------------------------------------------
# Branch 2: Etched (frame_effects contains 'etched' OR finish == 'etched')
# ---------------------------------------------------------------------------


def test_etched_via_frame_effects():
    assert derive_variant_label("nonfoil", None, "etched", None) == "Etched Foil"


def test_etched_via_finish():
    assert derive_variant_label("etched", None, "etched", None) == "Etched Foil"


def test_etched_finish_only():
    """finish='etched' alone (without frame_effects) also triggers Etched Foil."""
    assert derive_variant_label("etched", None, None, None) == "Etched Foil"


# ---------------------------------------------------------------------------
# Branch 3: Showcase (frame_effects contains 'showcase')
# ---------------------------------------------------------------------------


def test_showcase_nonfoil():
    assert derive_variant_label("nonfoil", None, "showcase", None) == "Showcase"


def test_showcase_foil():
    assert derive_variant_label("foil", None, "showcase", None) == "Showcase Foil"


# ---------------------------------------------------------------------------
# Branch 4: Extended Art (frame_effects contains 'extendedart')
# ---------------------------------------------------------------------------


def test_extendedart_nonfoil():
    assert derive_variant_label("nonfoil", None, "extendedart", None) == "Extended Art"


def test_extendedart_foil():
    assert derive_variant_label("foil", None, "extendedart", None) == "Extended Art Foil"


# ---------------------------------------------------------------------------
# Branch 5: Borderless (border_color == 'borderless')
# ---------------------------------------------------------------------------


def test_borderless_nonfoil():
    assert derive_variant_label("nonfoil", None, None, "borderless") == "Borderless"


def test_borderless_foil():
    assert derive_variant_label("foil", None, None, "borderless") == "Borderless Foil"


# ---------------------------------------------------------------------------
# Branch 6: Foil (finish == 'foil', no special treatments)
# ---------------------------------------------------------------------------


def test_foil_plain():
    assert derive_variant_label("foil", None, None, None) == "Foil"


# ---------------------------------------------------------------------------
# Branch 7: Regular (fallback — nonfoil, no special treatments)
# ---------------------------------------------------------------------------


def test_regular():
    assert derive_variant_label("nonfoil", None, None, None) == "Regular"


def test_regular_empty_finish():
    """Empty string finish should also default to Regular."""
    assert derive_variant_label("", None, None, None) == "Regular"


# ---------------------------------------------------------------------------
# Acceptance-criteria checks from tasks.md
# ---------------------------------------------------------------------------


def test_acceptance_foil():
    assert derive_variant_label("foil", None, None, None) == "Foil"


def test_acceptance_borderless():
    assert derive_variant_label("nonfoil", None, None, "borderless") == "Borderless"


def test_acceptance_showcase_foil():
    assert derive_variant_label("foil", None, "showcase", None) == "Showcase Foil"


def test_acceptance_etched_foil():
    assert derive_variant_label("etched", None, "etched", None) == "Etched Foil"


def test_acceptance_serialized():
    assert derive_variant_label("nonfoil", "serialized", None, None) == "Serialized"
