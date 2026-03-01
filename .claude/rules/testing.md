---
paths:
  - "tests/**"
---

# Testing Conventions

- pytest is the test runner. Run from repo root: `pytest tests/`.
- All tests live in `tests/` directory only. No test files inside `deckdex/`, `backend/`, or `frontend/src/`.
- Mock external APIs: Scryfall, Google Sheets, OpenAI. Never make real HTTP calls in tests.
- Test files: `test_<module>.py`. Test functions: `test_<behavior>`.
- Use `unittest.mock` or `pytest` fixtures for mocking. Prefer `@patch` for external dependencies.
- Type hints on test functions are optional but encouraged for complex fixtures.
