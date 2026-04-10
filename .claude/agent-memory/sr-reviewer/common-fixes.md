---
name: Common CI Fixes
description: Recurring patterns that fail CI and their fixes
type: feedback
---

## dndkit-mock-cast

When writing tests that mock `useDraggable` from `@dnd-kit/core` and overriding return values with `mockReturnValueOnce`, the stub object must be cast through `unknown` first:

```ts
// WRONG — TS2352
vi.mocked(useDraggable).mockReturnValueOnce({ ... } as ReturnType<typeof useDraggable>);

// CORRECT
vi.mocked(useDraggable).mockReturnValueOnce({ ... } as unknown as ReturnType<typeof useDraggable>);
```

**Why:** The full `useDraggable` return type has 10+ fields. A partial mock doesn't overlap enough for a direct cast.

## unused-vitest-imports

Test files that use real i18n translations (handled by `src/test/setup.ts`) do not need `vi.mock('react-i18next')` and therefore don't need `vi` imported. `beforeEach` is only needed if there is actual per-test setup.

ESLint `@typescript-eslint/no-unused-vars` treats these as errors.

**Fix:** Remove unused `vi` and `beforeEach` imports from test files that have no mock calls or per-test setup.

## preexisting-ts-errors

The following TypeScript errors exist in the codebase and pre-date any current changes. Do NOT attempt to fix them as part of frontend review — they are out of scope:

- `src/components/ActiveJobs.tsx(212,17)`: TS2322
- `src/components/CardFormModal.tsx(91,28)` and `(92,51)`: TS2345/TS2339
- `src/components/DeckCardPickerModal.tsx(54,22)`: TS2488
- `src/components/JobLogModal.tsx(86,73)`: TS2322
- `src/components/PriceChart.tsx(73,13)`: TS2322
- `src/hooks/useApi.ts(217,22)`: TS2345
- `src/pages/Import.tsx(55,20)`: TS2554

The build command used in review already filters some of these with grep -v patterns.

## pydantic-v2-configdict

New Pydantic v2 models must use `model_config = ConfigDict(from_attributes=True)` as a class attribute instead of the deprecated `class Config: from_attributes = True`. The old form still works but generates deprecation warnings that pollute test output and will break in Pydantic v3.

**Fix:**
```python
# WRONG — deprecated
class MyModel(BaseModel):
    class Config:
        from_attributes = True

# CORRECT
from pydantic import BaseModel, ConfigDict
class MyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

**Why:** Pydantic V2 uses `model_config` as the preferred API. `class Config` is a compatibility shim scheduled for removal in V3.

## openspec-archive-invocation

`openspec archive` takes a **change name** (not a path). Passing a directory path returns `Error: Change '...' not found`.

**Correct:**
```bash
openspec archive multi-variant-collection-view -y
```

**Wrong:**
```bash
openspec archive openspec/changes/multi-variant-collection-view/ -y
```

**Why:** The CLI resolves the change name against the configured changes directory internally.

## ruff-import-order-and-unused

Developer agents frequently produce Python files with two ruff violations that need auto-fix before CI:

1. **I001** — Import block un-sorted or un-formatted. Occurs when stdlib imports and third-party/local imports are not separated by a blank line, or when imports within a block are not alphabetically ordered.
2. **F401** — Unused import. Common offenders: `typing.Optional`, `typing.Any`, `typing.Dict`, `unittest.mock.patch`, `pytest` (in files that don't use fixtures).

**Fix:** Run `ruff check . --fix && ruff format .` — all 20 violations fixed automatically.

**Why:** Generated code often includes imports that were needed during scaffolding but become unused after implementation. Also, stdlib-before-third-party block ordering is non-obvious to generators.

**File patterns:** `tests/test_*.py`, `deckdex/storage/*.py`, `backend/api/routes/*.py`, `backend/api/services/*.py`
