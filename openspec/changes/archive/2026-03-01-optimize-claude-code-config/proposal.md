## Why

Claude Code loads the full root CLAUDE.md (112 lines) plus scoped CLAUDE.md files on every session, regardless of which layer is being worked on. There are no permission rules (`.claude/settings.json`), so Claude asks for approval on routine operations (pytest, git, npm). There are no conditional rules (`.claude/rules/`), so layer-specific conventions consume tokens even when irrelevant. This wastes context, creates friction, and reduces accuracy.

## What Changes

- **Create `.claude/settings.json`**: Permission rules that auto-allow safe operations (pytest, git, npm, lint, ruff) and deny dangerous ones (rm -rf, curl to external URLs, reading .env files). Eliminates repetitive permission prompts.
- **Create `.claude/rules/`**: Four conditional rule files that load only when Claude reads files in the matching layer — `backend.md`, `frontend.md`, `core.md`, `testing.md`. Conventions currently duplicated between root CLAUDE.md and scoped CLAUDE.md files move here with path-based activation.
- **Slim down root CLAUDE.md**: Remove layer-specific conventions (now in rules/), remove verbose sections that repeat what rules/ covers. Target: under 80 lines of essential project-wide context.

## Capabilities

### New Capabilities
- None (this is a configuration/tooling change, not a feature)

### Modified Capabilities
- None (no application code changes)

## Impact

- **Files created**: `.claude/settings.json`, `.claude/rules/backend.md`, `.claude/rules/frontend.md`, `.claude/rules/core.md`, `.claude/rules/testing.md`
- **Files modified**: `CLAUDE.md` (slimmed down)
- **Files unchanged**: `backend/CLAUDE.md`, `frontend/CLAUDE.md`, `deckdex/CLAUDE.md` (kept as-is — they still serve as entry points for scoped context; rules/ supplements, not replaces them)
- **Dependencies**: None
- **Risk**: Low — configuration only, no application code changes

## Non-goals

- MCP server configuration — explicitly excluded per user request
- Deleting scoped CLAUDE.md files — they remain as lightweight pointers
- Adding hooks beyond what already exists (stop-hook-git-check.sh)
- Changing OpenSpec configuration (already enriched separately)
