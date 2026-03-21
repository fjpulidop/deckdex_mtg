"""Unit tests for deck snapshot diff logic in deck_repository.py.

Tests exercise _compute_diff which is a pure function — no database required.
All fixtures use scope="function" per project testing conventions.
"""

from deckdex.storage.deck_repository import _compute_diff

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def snapshot_entry(card_id: int, name: str, qty: int, is_commander: bool = False) -> dict:
    return {"card_id": card_id, "name": name, "quantity": qty, "is_commander": is_commander}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_compute_diff_empty_before():
    """All cards show up as added when before is empty (first snapshot)."""
    after = [snapshot_entry(1, "Sol Ring", 1), snapshot_entry(2, "Lightning Bolt", 4)]
    diff = _compute_diff(before=[], after=after)
    assert len(diff["added"]) == 2
    assert diff["removed"] == []
    assert diff["quantity_changed"] == []
    assert diff["commander_changed"] is None


def test_compute_diff_added_card():
    """A card present in after but not before appears in added."""
    before = [snapshot_entry(1, "Sol Ring", 1)]
    after = [snapshot_entry(1, "Sol Ring", 1), snapshot_entry(2, "Lightning Bolt", 4)]
    diff = _compute_diff(before=before, after=after)
    assert len(diff["added"]) == 1
    assert diff["added"][0]["card_id"] == 2
    assert diff["added"][0]["name"] == "Lightning Bolt"
    assert diff["added"][0]["quantity"] == 4
    assert diff["removed"] == []
    assert diff["quantity_changed"] == []


def test_compute_diff_removed_card():
    """A card present in before but not after appears in removed."""
    before = [snapshot_entry(1, "Sol Ring", 1), snapshot_entry(2, "Lightning Bolt", 4)]
    after = [snapshot_entry(1, "Sol Ring", 1)]
    diff = _compute_diff(before=before, after=after)
    assert diff["added"] == []
    assert len(diff["removed"]) == 1
    assert diff["removed"][0]["card_id"] == 2
    assert diff["removed"][0]["name"] == "Lightning Bolt"
    assert diff["quantity_changed"] == []


def test_compute_diff_quantity_changed():
    """Same card_id with a different quantity appears in quantity_changed."""
    before = [snapshot_entry(1, "Sol Ring", 1)]
    after = [snapshot_entry(1, "Sol Ring", 3)]
    diff = _compute_diff(before=before, after=after)
    assert diff["added"] == []
    assert diff["removed"] == []
    assert len(diff["quantity_changed"]) == 1
    change = diff["quantity_changed"][0]
    assert change["card_id"] == 1
    assert change["old_quantity"] == 1
    assert change["new_quantity"] == 3


def test_compute_diff_commander_changed():
    """commander_changed is set when the commander card changes."""
    before = [snapshot_entry(1, "Sol Ring", 1), snapshot_entry(2, "Atraxa", 1, is_commander=True)]
    after = [snapshot_entry(1, "Sol Ring", 1), snapshot_entry(3, "Korvold", 1, is_commander=True)]
    diff = _compute_diff(before=before, after=after)
    assert diff["commander_changed"] == "Korvold"


def test_compute_diff_commander_unchanged():
    """commander_changed is None when the same card is commander in both snapshots."""
    before = [snapshot_entry(1, "Sol Ring", 1), snapshot_entry(2, "Atraxa", 1, is_commander=True)]
    after = [snapshot_entry(1, "Sol Ring", 1), snapshot_entry(2, "Atraxa", 1, is_commander=True)]
    diff = _compute_diff(before=before, after=after)
    assert diff["commander_changed"] is None


def test_compute_diff_no_changes():
    """Identical before and after produces an empty diff with commander_changed=None."""
    state = [
        snapshot_entry(1, "Sol Ring", 1),
        snapshot_entry(2, "Lightning Bolt", 4),
        snapshot_entry(3, "Atraxa", 1, is_commander=True),
    ]
    diff = _compute_diff(before=state, after=state)
    assert diff["added"] == []
    assert diff["removed"] == []
    assert diff["quantity_changed"] == []
    assert diff["commander_changed"] is None


def test_compute_diff_both_empty():
    """Empty before and empty after yields a completely empty diff."""
    diff = _compute_diff(before=[], after=[])
    assert diff["added"] == []
    assert diff["removed"] == []
    assert diff["quantity_changed"] == []
    assert diff["commander_changed"] is None


def test_compute_diff_combined_changes():
    """A single diff can contain added, removed, and quantity_changed simultaneously."""
    before = [
        snapshot_entry(1, "Sol Ring", 1),
        snapshot_entry(2, "Lightning Bolt", 4),
        snapshot_entry(3, "Counterspell", 2),
    ]
    after = [
        snapshot_entry(1, "Sol Ring", 3),  # quantity changed
        snapshot_entry(2, "Lightning Bolt", 4),  # unchanged
        snapshot_entry(4, "Brainstorm", 4),  # added
        # card_id=3 (Counterspell) removed
    ]
    diff = _compute_diff(before=before, after=after)
    assert len(diff["added"]) == 1
    assert diff["added"][0]["card_id"] == 4
    assert len(diff["removed"]) == 1
    assert diff["removed"][0]["card_id"] == 3
    assert len(diff["quantity_changed"]) == 1
    qc = diff["quantity_changed"][0]
    assert qc["card_id"] == 1
    assert qc["old_quantity"] == 1
    assert qc["new_quantity"] == 3


def test_compute_diff_quantity_decreased():
    """Quantity decrease is captured correctly (old > new)."""
    before = [snapshot_entry(1, "Sol Ring", 4)]
    after = [snapshot_entry(1, "Sol Ring", 1)]
    diff = _compute_diff(before=before, after=after)
    assert len(diff["quantity_changed"]) == 1
    qc = diff["quantity_changed"][0]
    assert qc["old_quantity"] == 4
    assert qc["new_quantity"] == 1


def test_compute_diff_commander_removed():
    """When commander is present in before but absent in after, commander_changed reflects the new state."""
    before = [snapshot_entry(1, "Atraxa", 1, is_commander=True)]
    after = [snapshot_entry(1, "Atraxa", 1, is_commander=False)]
    diff = _compute_diff(before=before, after=after)
    # After has no commander — commander_after is None; before had one — so they differ.
    # The implementation returns commander_after (None) when it differs from commander_before.
    assert diff["commander_changed"] is None


def test_compute_diff_large_diff():
    """Handles a deck with many cards correctly (stress check for keying logic)."""
    n = 100
    before = [snapshot_entry(i, f"Card {i}", i % 4 + 1) for i in range(1, n + 1)]
    # Remove even card_ids, double quantity of odds, add new card_ids 200-209
    after = [snapshot_entry(i, f"Card {i}", (i % 4 + 1) * 2) for i in range(1, n + 1, 2)] + [
        snapshot_entry(200 + j, f"New Card {j}", 1) for j in range(10)
    ]
    diff = _compute_diff(before=before, after=after)

    # All even cards (1..100) removed = 50 removals
    assert len(diff["removed"]) == 50
    # 10 new cards added
    assert len(diff["added"]) == 10
    # All odd cards had their quantity doubled = 50 quantity changes
    assert len(diff["quantity_changed"]) == 50
