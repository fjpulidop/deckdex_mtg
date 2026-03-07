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

### Cross-Feature Merge Issues
- Parallel developers may both modify `en.json`/`es.json` — check for merge conflicts in i18n files
- Shared files like `client.ts`, `useApi.ts` may have duplicate type definitions
- Import ordering in files modified by multiple developers

## Links
- See `common-failures.md` for detailed examples (create when needed)
