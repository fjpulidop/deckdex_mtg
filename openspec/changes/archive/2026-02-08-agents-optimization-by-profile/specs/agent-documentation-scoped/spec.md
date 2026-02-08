## ADDED Requirements

### Requirement: Thin root AGENTS.md with precedence and index

The repository root SHALL contain a single `AGENTS.md` that is kept thin. It MUST state the precedence rule (e.g. "the closest AGENTS.md to the files you are changing wins; root holds global defaults only"). It MUST include an "Index of scoped AGENTS.md" section that lists exactly the scoped files: `backend/AGENTS.md`, `frontend/AGENTS.md`, and `deckdex/AGENTS.md`, each with a brief description of the scope. Root SHALL NOT duplicate stack-specific content (commands, file maps, golden samples) that belong in scoped files; it MAY retain project-wide content such as skills and workflow.

#### Scenario: Root file is thin and points to scoped files

- **WHEN** a reader opens the root AGENTS.md
- **THEN** they see a precedence rule, the index of scoped AGENTS.md (backend, frontend, deckdex), and project-wide sections (e.g. skills); they do not see full backend/frontend/deckdex commands or file maps in root

### Requirement: Backend scoped AGENTS.md

The repository SHALL contain `backend/AGENTS.md`. It MUST describe only the backend scope (API: FastAPI, routes, services, Docker). It SHALL include at least: overview, commands (install, lint, test, run) relevant to the backend, a file map for directories under `backend/`, and conventions or golden samples for backend code. It MAY reference the root AGENTS.md for project-wide skills and workflow.

#### Scenario: Backend file exists and is self-contained for backend

- **WHEN** a reader opens `backend/AGENTS.md`
- **THEN** they see backend-specific commands and structure; they do not see frontend or deckdex-specific content in this file

### Requirement: Frontend scoped AGENTS.md

The repository SHALL contain `frontend/AGENTS.md`. It MUST describe only the frontend scope (React, TypeScript, Vite). It SHALL include at least: overview, commands (install, lint, test, build, dev) relevant to the frontend, a file map for directories under `frontend/`, and conventions or golden samples for frontend code. It MAY reference the root AGENTS.md for project-wide skills and workflow.

#### Scenario: Frontend file exists and is self-contained for frontend

- **WHEN** a reader opens `frontend/AGENTS.md`
- **THEN** they see frontend-specific commands and structure; they do not see backend or deckdex-specific content in this file

### Requirement: Deckdex scoped AGENTS.md

The repository SHALL contain `deckdex/AGENTS.md`. It MUST describe only the deckdex package scope (core library/CLI: processor, storage, config). It SHALL include at least: overview, commands relevant to deckdex (if any, e.g. tests), a file map for `deckdex/` (and subpackages such as `storage/`), and conventions or golden samples for deckdex code. It MAY reference the root AGENTS.md for project-wide skills and workflow.

#### Scenario: Deckdex file exists and is self-contained for deckdex

- **WHEN** a reader opens `deckdex/AGENTS.md`
- **THEN** they see deckdex-specific structure and conventions; they do not see backend or frontend-specific content in this file

### Requirement: No duplication of stack content in root

Root AGENTS.md SHALL NOT contain full command tables, file maps, or golden samples that are specific to backend, frontend, or deckdex. Those MUST live only in the corresponding scoped file. Root MAY contain a short file map that describes top-level directories (e.g. backend/, frontend/, deckdex/) at a single line each if that aids navigation without duplicating scoped content.

#### Scenario: Root does not duplicate scoped content

- **WHEN** comparing root AGENTS.md with backend/AGENTS.md, frontend/AGENTS.md, and deckdex/AGENTS.md
- **THEN** detailed backend commands/file map are only in backend/AGENTS.md; detailed frontend commands/file map only in frontend/AGENTS.md; detailed deckdex file map/conventions only in deckdex/AGENTS.md
