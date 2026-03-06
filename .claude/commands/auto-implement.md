# Auto-Implement: Full OpenSpec Lifecycle

Take a feature description and execute the complete OpenSpec lifecycle autonomously, from spec creation to implementation to archival. No user interaction required.

**Input:** $ARGUMENTS (a natural language description of what to build, e.g. "add a price history chart to analytics")

**CRITICAL: This command runs fully autonomously. Never ask the user for clarification — not via AskUserQuestion, not by stopping and waiting. Make reasonable decisions and keep moving. If something is ambiguous, pick the simplest sensible option and document your choice in the artifacts.**

---

## Phase 1: Setup

Derive a kebab-case change name from the description (e.g. "add a price history chart" -> `add-price-history-chart`).

If a change with that name already exists, append `-v2`, `-v3`, etc.

## Phase 2: Fast-Forward (create all artifacts)

Use the **Skill tool** to invoke `openspec-ff-change` with the derived change name:

```
Skill: openspec-ff-change
Arguments: <change-name>
```

This runs the full OpenSpec fast-forward workflow:
- Creates the change via `openspec new change`
- Loops through artifacts in dependency order using `openspec status --json` and `openspec instructions --json`
- Creates proposal, design, delta-spec, tasks (or whatever the schema requires)

**Override for autonomy:** When the skill would normally use AskUserQuestion, instead make a reasonable decision based on the input description and codebase context. The input description IS the user's intent — no further clarification needed.

**Artifact quality guidelines:**
- Proposal: concise, focused on the "what" and "why"
- Design: reference actual file paths, existing patterns, and real code structures — read code first
- Delta-spec: only include sections that change
- Tasks: atomic, ordered, each with clear acceptance criteria. Include test tasks.

## Phase 3: Implement (apply all tasks)

Use the **Skill tool** to invoke `openspec-apply-change` with the change name:

```
Skill: openspec-apply-change
Arguments: <change-name>
```

This runs the full OpenSpec apply workflow:
- Gets apply instructions via `openspec instructions apply --json`
- Reads all context files
- Implements each task sequentially, marking `- [ ]` -> `- [x]`

**Override for autonomy:** When the skill would normally pause to ask for clarification on a task, instead make a reasonable decision and add a brief comment in the code explaining the choice. Never stop.

**Implementation guidelines (apply these during task execution):**
- Follow existing codebase patterns exactly (check similar files first)
- Backend: thin routes, services for logic, Pydantic models for responses
- Frontend: functional components, TanStack Query, Tailwind, strict TypeScript, i18n keys in both en.json and es.json
- Tests: pytest functions in `tests/`, mock external deps, use `dependency_overrides` for FastAPI (with setUp/tearDown per test class, NOT module-level overrides)
- Core: no framework imports, config via config_loader, DB via repository

## Phase 4: Verify

Run verification checks:

```bash
# TypeScript
cd /Users/javi/repos/deckdex_mtg/frontend && npx tsc --noEmit

# Backend tests
cd /Users/javi/repos/deckdex_mtg && ./venv/bin/pytest tests/ -q
```

If tests fail, fix the issues and re-run (up to 3 attempts). Do not proceed to archive with failing tests.

## Phase 5: Archive

Use the **Skill tool** to invoke `openspec-archive-change` with the change name:

```
Skill: openspec-archive-change
Arguments: <change-name>
```

This runs the full OpenSpec archive workflow:
- Checks artifact and task completion via `openspec status --json`
- Syncs delta specs to main specs if they exist
- Moves the change to `openspec/changes/archive/YYYY-MM-DD-<name>/`

**Override for autonomy:** When the skill would normally prompt for confirmation (incomplete tasks, sync choice), auto-confirm and sync. Always sync delta specs before archiving.

## Phase 6: Report

Print a summary table:

| Step | Status |
|------|--------|
| Change created | `<name>` |
| Artifacts | list of created artifacts |
| Tasks implemented | N/N |
| TypeScript | pass/fail |
| Tests | pass/fail (count) |
| Archived to | path |

List any files created or modified.

---

## Error Handling

- If `openspec new change` fails (name exists): append `-v2` suffix and retry
- If artifact creation is unclear: make the simplest reasonable choice, note it
- If implementation hits an issue: try to fix it, if truly blocked skip the task and note it in the report
- If tests fail after implementation: fix the failing tests (up to 3 attempts), then report
- Never stop the pipeline for a non-critical issue. Always produce a final report.
