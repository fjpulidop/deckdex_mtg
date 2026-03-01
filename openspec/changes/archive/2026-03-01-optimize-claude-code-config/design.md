## Context

Claude Code loads CLAUDE.md files at session start and on-demand when reading files in subdirectories. Currently, all conventions (backend, frontend, core, testing) are loaded regardless of what's being worked on. There are no permission rules, causing Claude to prompt for approval on routine dev commands. The `.claude/rules/` mechanism allows path-gated rules that only load when Claude reads matching files — this is the key optimization lever.

The user already has a global `~/.claude/settings.json` with a Stop hook (git-check) and `"permissions": {"allow": ["Skill"]}`. The project has no `.claude/settings.json`.

## Goals / Non-Goals

**Goals:**
- Reduce permission friction by auto-allowing safe dev operations
- Reduce token consumption by loading layer rules only when relevant
- Slim root CLAUDE.md to essential project-wide context only
- Maintain all existing conventions — reorganize, don't lose

**Non-Goals:**
- MCP server configuration (excluded per user)
- Deleting scoped CLAUDE.md files (they serve as directory context)
- Adding new hooks
- Changing any application code

## Decisions

### 1. Permission rules: allow-list approach for dev commands

**Choice:** Explicit allow-list for known safe operations. Deny-list for dangerous patterns.

```json
{
  "permissions": {
    "allow": [
      "Bash(pytest *)",
      "Bash(python -m pytest *)",
      "Bash(git *)",
      "Bash(npm run *)",
      "Bash(npm install *)",
      "Bash(npx *)",
      "Bash(cd frontend && npm *)",
      "Bash(uvicorn *)",
      "Bash(pip install *)",
      "Bash(ruff *)",
      "Bash(python main.py *)",
      "Bash(docker compose *)",
      "Bash(ls *)",
      "Bash(mkdir *)",
      "Bash(cat *)",
      "Bash(wc *)",
      "Bash(find *)",
      "Bash(python3 *)",
      "Bash(python -c *)",
      "Skill"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Read(.env*)",
      "Read(**/credentials*)"
    ]
  }
}
```

**Rationale:** Covers all commands from CLAUDE.md dev commands section plus common exploration patterns. Deny-list prevents accidental destructive ops and secret file reads.

### 2. Rules directory: one file per layer with path frontmatter

**Choice:** Four rule files, each scoped with `paths:` frontmatter:

| File | Paths | Content Source |
|------|-------|----------------|
| `backend.md` | `backend/**` | `backend/CLAUDE.md` conventions + additional patterns |
| `frontend.md` | `frontend/**` | `frontend/CLAUDE.md` conventions + additional patterns |
| `core.md` | `deckdex/**` | `deckdex/CLAUDE.md` conventions + additional patterns |
| `testing.md` | `tests/**` | Testing conventions from specs/conventions.md |

**Alternative considered:** One monolithic rules file without paths. Rejected — defeats the purpose of conditional loading.

**Rationale:** Each file loads only when Claude reads files in that layer. A backend-only change never loads frontend rules, saving ~50-80 tokens per rule file avoided.

### 3. Scoped CLAUDE.md files: keep as-is

**Choice:** Don't modify `backend/CLAUDE.md`, `frontend/CLAUDE.md`, `deckdex/CLAUDE.md`.

**Rationale:** They serve as lightweight context when Claude enters a directory — file maps, commands, and brief conventions. The rules/ files supplement them with deeper guardrails. Removing them would lose the "what's in this directory" context that's useful for orientation. There's minimal duplication cost since they're small (< 35 lines each).

### 4. Root CLAUDE.md: keep structure, remove what's now conditional

**Choice:** Slim CLAUDE.md by:
- Keep: project description, stack table, repo layout, dev commands, environment, architecture diagram, warnings, OpenSpec section, scoped context pointers
- Remove: Conventions section (6 bullet points → now in rules/)
- Result: ~75 lines (down from 112)

**Alternative considered:** Aggressive cut to ~40 lines. Rejected — dev commands and architecture diagram are essential context that should always load.

**Rationale:** The Conventions section is the only content that's purely layer-specific. Everything else is project-wide context that's useful regardless of what layer is being worked on.

### 5. Rules content: enriched beyond current CLAUDE.md

**Choice:** Each rule file includes not just the current conventions but additional guardrails discovered from specs and patterns:

- **backend.md**: Pydantic response models, dependency injection via `dependencies.py`, router registration in `main.py`, service placement in `services/`
- **frontend.md**: TanStack Query patterns, `api/client.ts` as single API layer, ThemeContext usage, component placement conventions
- **core.md**: Zero framework imports rule, config_loader as single config source, repository as single DB layer, Scryfall client patterns
- **testing.md**: Test file naming, mock patterns for external APIs, test location in `tests/` only

**Rationale:** Rules are the right place for detailed guardrails — they load conditionally, so verbosity here doesn't cost tokens when working on other layers.

## Risks / Trade-offs

**[Low] Permission rules too broad** → `Bash(git *)` allows any git command including destructive ones like `git push --force`. Mitigation: Claude's built-in safety already warns on destructive git ops. The allow-list prevents the prompt for routine `git status`, `git add`, `git commit`.

**[Low] Rules duplication with scoped CLAUDE.md** → Some conventions appear in both places. Mitigation: Scoped CLAUDE.md files are brief (commands + file map) and provide directory orientation. Rules provide detailed guardrails. The overlap is minimal and both serve different purposes.

**[None] No application code risk** → This change only affects Claude Code configuration files. Zero risk of breaking application behavior.
