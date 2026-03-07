# Reviewer Agent Memory

## Common CI Failure Patterns

### Backend
- `ruff format --check` fails when developers only run `ruff check` — always run both
- Import sorting (`I001`) is caught by `ruff check` but formatting issues need `ruff format`
- New test files often have unused imports (e.g., `from unittest.mock import call` unused)

### Frontend
- `react-hooks/set-state-in-effect`: ESLint rule that bans direct `setState` calls in useEffect body. Functional updaters `setState(prev => ...)` are also flagged. Fix: use `useSyncExternalStore` for external store patterns, or move state derivation out of effects.
- Unused eslint-disable directives cause warnings that can become errors depending on config
- `npm run lint` catches things `tsc --noEmit` does not — always run both

### Test Isolation
- **Module-level `app.dependency_overrides`**: Setting auth overrides at module scope (outside any test class/function) causes cross-test pollution — another test's `tearDown` calling `.pop()` or `.clear()` will remove it, causing 401s in subsequent tests even when run in isolation they pass. Always use `setUp`/`tearDown` per test class. Tests pass in isolation but fail in full `pytest tests/` run.
- **`scope="module"` pytest fixtures with `MagicMock`**: The mock accumulates call history across all tests in the module. `assert_not_called()` / `assert_called_once()` on a shared mock will fail on later tests even if the individual test doesn't call the method. Fix: use `scope="function"` for fixtures that yield `MagicMock` repos.

### Test Bugs
- **`tempfile.TemporaryDirectory()` with context manager**: Assertions that check file existence MUST be inside the `with` block. If placed outside (after the `with` ends), the directory is already deleted and all `exists()` checks return `False`.
- **Validation error status codes**: This project's `validation_exception_handler` converts ALL Pydantic `RequestValidationError` to HTTP 400 (not the FastAPI default of 422). Tests asserting on Pydantic validation failures must expect 400, not 422.

### Cross-Feature Merge Issues
- Parallel developers may both modify `en.json`/`es.json` — check for merge conflicts in i18n files
- Shared files like `client.ts`, `useApi.ts` may have duplicate type definitions
- Import ordering in files modified by multiple developers

## Links
- See `common-failures.md` for detailed examples (create when needed)
