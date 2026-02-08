# Agent documentation (scoped)

AGENTS.md split by scope; root thin, detail in scoped files.

### Requirements (compact)

- **Root:** One root `AGENTS.md`, thin. State precedence: "closest AGENTS.md to files you change wins; root = global defaults." Index of scoped files: backend, frontend, deckdex (each with brief scope). No duplicate stack-specific commands/file maps in root; project-wide content (skills, workflow) OK.
- **backend/AGENTS.md:** Backend only (FastAPI, routes, services, Docker). Overview, commands (install, run, lint), file map for backend/, conventions. Reference root for skills.
- **frontend/AGENTS.md:** Frontend only (React, TS, Vite). Overview, commands (install, dev, build, lint), file map for frontend/, conventions. Reference root for skills.
- **deckdex/AGENTS.md:** Deckdex only (core/CLI: processor, storage, config). Overview, commands, file map for deckdex/, conventions. Reference root for skills.
- **No duplication:** Detailed commands and file maps for each stack live only in that scope’s file.
