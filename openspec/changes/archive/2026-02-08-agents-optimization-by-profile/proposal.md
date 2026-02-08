## Why

LLMs interacting with the repo today receive a single root AGENTS.md that mixes project-wide skills with no stack-specific guidance. Loading one large context for every request wastes tokens when work is scoped to one area (e.g. frontend-only). Splitting agent documentation by profile (backend, frontend, deckdex) with a thin root and an index reduces token usage and keeps each conversation focused on the relevant stack.

## What Changes

- **Thin root AGENTS.md**: Keep purpose, skills list, and workflow; add precedence rule ("closest AGENTS.md wins") and an **Index of scoped AGENTS.md** pointing to backend, frontend, and deckdex. No duplication of stack-specific content in root.
- **backend/AGENTS.md**: New scoped file for API (FastAPI, routes, services, Docker). Commands, file map, conventions, and golden samples for the backend only.
- **frontend/AGENTS.md**: New scoped file for the web app (React, TypeScript, Vite). Commands, file map, conventions, and golden samples for the frontend only.
- **deckdex/AGENTS.md**: New scoped file for the core library/CLI (processor, storage, config). Commands, file map, and conventions for the deckdex package only.

## Capabilities

### New Capabilities

- `agent-documentation-scoped`: Defines how AGENTS.md is structured by profile (root + backend, frontend, deckdex), precedence rules, index in root, and what each scoped file must contain so that token usage is optimized and agents get only the context relevant to the files they are editing.

### Modified Capabilities

- (none)

## Impact

- **Root AGENTS.md**: Refactored to be thin; adds precedence and index; skills section unchanged.
- **New files**: `backend/AGENTS.md`, `frontend/AGENTS.md`, `deckdex/AGENTS.md` (documentation only; no application code or dependencies changed).
