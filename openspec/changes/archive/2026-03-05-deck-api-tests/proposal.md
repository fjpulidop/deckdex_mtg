# Proposal: Deck API Route Tests

## Date
2026-03-05

## Status
Proposed

## Problem

The Deck API has 8 endpoints with ZERO test coverage. This is the largest untested surface in the backend. Decks require PostgreSQL and have complex relationships (deck_cards referencing cards), making them prone to regressions.

## Proposed Solution

Add `tests/test_decks.py` with comprehensive tests for all 8 deck endpoints:
- GET /api/decks/ (list)
- POST /api/decks/ (create)
- GET /api/decks/{id} (get with cards)
- PATCH /api/decks/{id} (update name)
- DELETE /api/decks/{id} (delete)
- POST /api/decks/{id}/cards (add card)
- PATCH /api/decks/{id}/cards/{card_id} (set commander)
- DELETE /api/decks/{id}/cards/{card_id} (remove card)

Mock strategy: Override `get_deck_repo` dependency to return a mock `DeckRepository`. Use pytest fixtures from `conftest.py` (not unittest.TestCase).

## Out of Scope
- Integration tests with real PostgreSQL
- Frontend component tests
- Import endpoint tests (separate change)
