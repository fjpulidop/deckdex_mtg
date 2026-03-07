# Auto-Implement: Full OpenSpec Lifecycle

Take a feature description and execute the complete OpenSpec lifecycle autonomously, using the architect agent for design and the developer agent for implementation. No user interaction required.

**Input:** $ARGUMENTS (a natural language description of what to build, e.g. "add a price history chart to analytics")

**CRITICAL: This command runs fully autonomously. Never ask the user for clarification — not via AskUserQuestion, not by stopping and waiting. Make reasonable decisions and keep moving. If something is ambiguous, pick the simplest sensible option and document your choice in the artifacts.**

---

## Phase 1: Setup

Derive a kebab-case change name from the description (e.g. "add a price history chart" -> `add-price-history-chart`).

If a change with that name already exists, append `-v2`, `-v3`, etc.

## Phase 2: Architect (design & artifacts)

Launch an **architect** agent (`subagent_type: architect`) to create all OpenSpec artifacts.

The architect's prompt should be:

> You are designing a feature autonomously. Create high-quality OpenSpec artifacts.
>
> **Description:** "<the input description>"
>
> Execute the OpenSpec design phase without any user interaction:
>
> 1. **Setup**: Change name is `<name>`.
> 2. **Create change**: Run `openspec new change "<name>"`.
> 3. **Read codebase**: Before writing any artifact, read the actual code files involved. Read relevant specs from `openspec/specs/`. Read layer-specific CLAUDE.md files and `.claude/rules/`. Understand existing patterns.
> 4. **Create artifacts** using `openspec status --json` and `openspec instructions --json`:
>    - **proposal.md**: What and why. Product motivation, scope, success criteria.
>    - **design.md**: Detailed technical design. Reference actual file paths, existing patterns, real code structures. Include impact analysis, architectural decisions with rationale, and risks/edge cases.
>    - **delta-spec**: Only sections that change from existing specs.
>    - **tasks.md**: Atomic, ordered tasks with clear acceptance criteria. Each task specifies files involved and what "done" looks like. Group by layer (Core → Backend → Frontend → Tests). Include test tasks.
>
> **Quality standards:**
> - Every artifact must reference real file paths and existing code patterns
> - Design decisions must be justified
> - Tasks must be self-contained and implementable without extra context
> - Include edge cases, error handling, and migration needs
>
> **Rules:**
> - Never ask for clarification. Make reasonable decisions and document your choices.
> - Read code before writing artifacts — ground everything in the actual codebase.
> - Use `openspec` CLI commands throughout.

Wait for the architect to complete. Verify artifacts exist in `openspec/changes/<name>/`.

## Phase 3: Implement (apply all tasks)

Launch a **developer** agent (`subagent_type: developer`) to implement from the architect's artifacts.

The developer's prompt should be:

> You are implementing a feature that has already been designed by an architect. The OpenSpec change artifacts are ready.
>
> **Change name:** "<name>"
>
> Execute the implementation phase without any user interaction:
>
> 1. **Read the architect's artifacts**: Read all files in `openspec/changes/<name>/`. These are your blueprint.
> 2. **Read context files**: Read every file referenced in the design and tasks.
> 3. **Implement**: Follow tasks.md in order. For each task, implement and mark done: `- [ ]` -> `- [x]`.
> 4. **Verify**: Run ALL checks — `ruff check .` (fix with `--fix` if needed), `cd frontend && npx tsc --noEmit`, `./venv/bin/pytest tests/ -q`, and `cd frontend && npx vitest run`. Fix failures (up to 3 attempts).
> 5. **Archive**: Run `openspec sync-specs` then `openspec archive change "<name>"`.
>
> **Rules:**
> - Never ask for clarification. The architect's artifacts have your answers.
> - Follow existing codebase patterns (check similar files before writing new ones).
> - Backend: thin routes, services for logic, Pydantic models.
> - Frontend: functional components, TanStack Query, Tailwind, strict TypeScript, i18n in en.json + es.json.
> - Tests: pytest functions in `tests/`, mock external deps, use `dependency_overrides` with setUp/tearDown per class (NOT module-level).
> - Use `openspec` CLI commands throughout.

Wait for the developer to complete.

## Phase 4: Verify, Commit & Report

**This phase is fully autonomous — do NOT ask the user for confirmation at any step.**

### 4a. Verify (must pass ALL checks)
1. Linting: `ruff check .` (fix with `ruff check . --fix` if needed)
2. TypeScript compiles: `cd frontend && npx tsc --noEmit`
3. Backend tests pass: `./venv/bin/pytest tests/ -q`
4. Frontend tests pass: `cd frontend && npx vitest run`
5. If failures, fix and re-verify (up to 3 attempts).

### 4b. Git commit and push
1. If on a shared/main branch, create a new branch: `git checkout -b feat/<change-name>`
2. Stage and commit with a descriptive message following existing commit style. End with `Co-Authored-By: Claude <noreply@anthropic.com>`.
3. Push: `git push -u origin <branch-name>`

### 4c. Report

Print a summary table:

| Step | Status |
|------|--------|
| Change created | `<name>` |
| Architect artifacts | list of created artifacts |
| Tasks implemented | N/N |
| TypeScript | pass/fail |
| Tests | pass/fail (count) |
| Committed | commit hash |
| Pushed to | branch name |
| Archived to | path |

List any files created or modified.

---

## Error Handling

- If `openspec new change` fails (name exists): append `-v2` suffix and retry
- If architect fails: fall back to developer-only mode (developer creates its own artifacts, like the old behavior)
- If developer hits an issue: try to fix it, if truly blocked skip the task and note it in the report
- If tests fail after implementation: fix the failing tests (up to 3 attempts), then report
- Never stop the pipeline for a non-critical issue. Always produce a final report.
