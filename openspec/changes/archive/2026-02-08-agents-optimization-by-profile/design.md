## Context

The repo has a single root `AGENTS.md` that documents Cursor skills (OpenSpec, create-rule, etc.) and general workflow. There is no stack-specific guidance for backend (FastAPI), frontend (React/Vite), or the deckdex core package. The agents.md convention (e.g. Netresearch skill) recommends a thin root plus scoped AGENTS.md per area, with "closest AGENTS.md wins" so that only relevant context is loaded per request. This change introduces that structure without altering application code or dependencies.

## Goals / Non-Goals

**Goals:**

- Reduce token usage for LLM interactions by loading only root + one scoped AGENTS.md when work is in a single area.
- Establish a thin root AGENTS.md with precedence rule and an index of scoped files.
- Add backend, frontend, and deckdex scoped AGENTS.md with commands, file map, conventions, and golden samples for each stack.
- Align with the pointer principle: root points to scoped files; no duplication of stack-specific content in root.

**Non-Goals:**

- Changing how Cursor or other tools select which AGENTS.md to inject (we document precedence; tool behavior is out of scope).
- Adding or changing .cursor/rules or other Cursor config beyond AGENTS.md files.
- Modifying application code, APIs, or dependencies.

## Decisions

1. **Three scopes: backend, frontend, deckdex**  
   Matches the three main areas of the repo (`backend/`, `frontend/`, `deckdex/`). Alternatives: a single "web" scope (backend + frontend) or more granular (e.g. `backend/api/`). Chosen for simplicity and clear stack boundaries; each scope has a distinct language and toolchain.

2. **Root remains the single place for skills**  
   OpenSpec and Cursor helper skills are project-wide and stay in root only. Scoped files do not list skills; they reference "root AGENTS.md for project-wide conventions/skills" where useful. This avoids duplication and keeps skills in one place.

3. **Scoped file structure follows convention**  
   Each scoped AGENTS.md includes: short overview, commands (verified where possible), file map, golden samples, and conventions/boundaries. Format and section names align with the agents skill references (e.g. thin root, scoped templates) so future automation or regeneration is easier.

4. **No automated generation for this change**  
   We write the four files (root + three scoped) by hand. Using the project's agents-skill scripts (e.g. generate-agents.sh) could be a later improvement; not in scope here to avoid dependency on that toolchain and to keep the change self-contained.

## Risks / Trade-offs

- **Cursor may load all AGENTS.md files**  
  If the IDE always injects every AGENTS.md in the repo, token savings are limited to avoiding duplication and keeping each file smaller. Mitigation: document precedence clearly so that at least the agent's behavior (which instructions win) is well-defined; actual injection is tool-dependent.

- **Drift between scoped files and code**  
  Commands, file maps, and golden samples can become outdated. Mitigation: keep scoped files concise, reference real paths and commands; recommend periodic review or a later step to run verify-content/verify-commands from the agents skill if adopted.

- **Discovery**  
  New contributors might not notice scoped AGENTS.md. Mitigation: root index lists them explicitly; precedence sentence in root directs readers to the nearest AGENTS.md.

## Migration Plan

- No runtime or deployable artifact; documentation only.
- Steps: (1) Create `backend/AGENTS.md`, `frontend/AGENTS.md`, `deckdex/AGENTS.md` with content per spec. (2) Refactor root `AGENTS.md`: add precedence and "Index of scoped AGENTS.md", remove any content that moves to scoped files (if present), keep skills and workflow. (3) No rollback beyond reverting the four file changes.

## Open Questions

- None for implementation. Optional follow-up: integrate with `.cursor/skills/agents` scripts (e.g. detect-scopes, generate-agents) for future updates.
