# Tasks: Deck API Route Tests

## Task 1 — Create test file with fixtures

**Files:** `tests/test_decks.py`

**What to do:**
1. Create `tests/test_decks.py`
2. Import app, TestClient, dependencies, DeckRepository
3. Create module-scoped `deck_client` fixture that overrides `require_deck_repo` with MagicMock and `get_current_user_id` with lambda: 1
4. Create sample data constants: SAMPLE_DECK, SAMPLE_DECK_WITH_CARDS
5. Ensure fixture cleanup restores dependency overrides

**Dependencies:** none

---

## Task 2 — List and Create deck tests

**Files:** `tests/test_decks.py`

**What to do:**
1. `test_list_decks_returns_list` — mock repo.list_all returning [SAMPLE_DECK], assert 200 + array
2. `test_list_decks_empty` — mock repo.list_all returning [], assert 200 + empty array
3. `test_create_deck_returns_201` — mock repo.create returning SAMPLE_DECK, POST with name, assert 201
4. `test_create_deck_default_name` — POST with empty body, verify repo.create called with "Unnamed Deck"

**Dependencies:** Task 1

---

## Task 3 — Get, Update, Delete deck tests

**Files:** `tests/test_decks.py`

**What to do:**
1. `test_get_deck_returns_with_cards` — mock repo.get_deck_with_cards returning SAMPLE_DECK_WITH_CARDS, assert 200 + cards array
2. `test_get_deck_not_found_returns_404` — mock returning None, assert 404
3. `test_update_deck_name` — mock repo.update_name returning updated deck, PATCH, assert 200
4. `test_update_deck_not_found` — mock returning None, assert 404
5. `test_delete_deck_returns_204` — mock repo.delete returning True, assert 204
6. `test_delete_deck_not_found` — mock returning False, assert 404

**Dependencies:** Task 1

---

## Task 4 — Card management tests

**Files:** `tests/test_decks.py`

**What to do:**
1. `test_add_card_to_deck` — mock repo.get_by_id + repo.add_card returning True + repo.get_deck_with_cards, POST card, assert 201
2. `test_add_card_not_in_collection` — mock repo.add_card returning False, assert 404
3. `test_add_card_deck_not_found` — mock repo.get_by_id returning None, assert 404
4. `test_set_commander` — mock repo.set_commander returning True + get_deck_with_cards, PATCH, assert 200
5. `test_set_commander_not_found` — mock returning False, assert 404
6. `test_remove_card_returns_204` — mock repo.remove_card returning True, assert 204
7. `test_remove_card_not_found` — mock returning False, assert 404

**Dependencies:** Task 1

---

## Task 5 — 501 without PostgreSQL test

**Files:** `tests/test_decks.py`

**What to do:**
1. `test_501_when_no_postgres` — temporarily override require_deck_repo to call the original (which checks get_deck_repo() → None), assert 501 on GET /api/decks/

**Dependencies:** Task 1

---

## Task 6 — Verification

**What to do:**
1. Run `pytest tests/test_decks.py -v` — all tests pass
2. Run `pytest tests/ -v` — existing tests still pass (no regressions)
3. Check no new lint warnings

**Dependencies:** Tasks 1-5
