## 1. Create `.claude/settings.json` with permission rules

- [x] 1.1 Create `.claude/settings.json` with allow-list for safe dev operations: `pytest`, `git`, `npm run`, `npm install`, `npx`, `uvicorn`, `pip install`, `ruff`, `python main.py`, `docker compose`, `ls`, `mkdir`, `python3`, `python -c`, `Skill`
- [x] 1.2 Add deny-list for dangerous operations: `rm -rf`, `curl`, `wget`, `Read(.env*)`, `Read(**/credentials*)`
- [x] 1.3 Verify JSON is valid and keys match Claude Code settings schema

## 2. Create `.claude/rules/` conditional rule files

- [x] 2.1 Create `.claude/rules/backend.md` with `paths: ["backend/**"]` frontmatter — include: thin routes pattern, Pydantic response models, dependency injection via `dependencies.py`, router registration in `main.py`, service placement in `services/`, WebSocket pattern from `progress.py`
- [x] 2.2 Create `.claude/rules/frontend.md` with `paths: ["frontend/**"]` frontmatter — include: all backend calls through `api/client.ts` + `useApi` hook, functional components only, Tailwind + ThemeContext for styling, TypeScript strict (no `any`), TanStack Query patterns, WebSockets only for job progress
- [x] 2.3 Create `.claude/rules/core.md` with `paths: ["deckdex/**"]` frontmatter — include: zero framework imports (no FastAPI, no React), config always via `config_loader.py`, all DB ops via `storage/repository.py`, secrets via env vars only, minimal dependencies (stdlib + requirements.txt)
- [x] 2.4 Create `.claude/rules/testing.md` with `paths: ["tests/**"]` frontmatter — include: pytest as test runner, all tests live in `tests/` directory only, mock external APIs (Scryfall, Google Sheets, OpenAI), test naming conventions, run tests from repo root

## 3. Slim down root CLAUDE.md

- [x] 3.1 Remove the "Conventions" section (6 bullet points) from root CLAUDE.md — this content is now covered by `.claude/rules/` files
- [x] 3.2 Verify remaining CLAUDE.md is under 80 lines and still contains: project description, stack table, repo layout, dev commands, environment, architecture diagram, warnings, OpenSpec section, scoped context pointers
- [x] 3.3 Add a brief note in CLAUDE.md pointing to `.claude/rules/` for layer-specific conventions
