# Auto-Implement: Full OpenSpec Lifecycle

Take a feature description and execute the complete OpenSpec lifecycle autonomously, using the architect agent for design, the developer agent for implementation, and the reviewer agent for CI validation. No user interaction required.

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
>    - **tasks.md**: Atomic, ordered tasks with clear acceptance criteria. Each task specifies files involved and what "done" looks like. Group by layer (Core -> Backend -> Frontend -> Tests). Include test tasks.
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
> 4. **Verify** with the full CI-equivalent suite:
>    - `ruff check .` (fix with `--fix` if needed)
>    - `ruff format --check .` (fix with `ruff format <file>` if needed)
>    - `./venv/bin/pytest tests/ -q`
>    - `cd frontend && npm run lint` (NOT just tsc — this catches ESLint rules like react-hooks)
>    - `cd frontend && npx tsc --noEmit`
>    - `cd frontend && npx vitest run`
>    Fix failures (up to 3 attempts).
> 5. **Archive**: Run `openspec sync-specs` then `openspec archive change "<name>"`.
>
> **Rules:**
> - Never ask for clarification. The architect's artifacts have your answers.
> - Follow existing codebase patterns (check similar files before writing new ones).
> - Backend: thin routes, services for logic, Pydantic models.
> - Frontend: functional components, TanStack Query, Tailwind, strict TypeScript, i18n in en.json + es.json.
> - Tests: pytest functions in `tests/`, mock external deps, use `dependency_overrides` with setUp/tearDown per class (NOT module-level).
> - **Test isolation**: All pytest fixtures with mocked repos/services MUST use `scope="function"` (NOT `scope="module"`). Module-scoped mocks cause cross-test pollution.
> - **Temp dir assertions**: All file-existence assertions MUST be inside the `with tempfile.TemporaryDirectory()` block — the directory is deleted when the block exits.
> - **HTTP status codes**: This project's `validation_exception_handler` converts Pydantic `RequestValidationError` to HTTP 400 (NOT 422). Always expect 400 for validation errors.
> - Use `openspec` CLI commands throughout.

Wait for the developer to complete.

## Phase 4: Review, Commit & Ship

**This phase is fully autonomous — do NOT ask the user for confirmation at any step.**

### 4a. Reviewer validation

Launch a **reviewer** agent (`subagent_type: reviewer`) to run CI-equivalent checks.

The reviewer's prompt should be:

> You are the final quality gate. The developer agent has completed implementation. Run the exact CI/CD pipeline checks and fix any issues.
>
> **Change name:** "<name>"
>
> Run the full CI-equivalent verification suite in this exact order:
>
> ### Backend
> 1. `ruff check .` — fix with `ruff check . --fix` if needed
> 2. `ruff format --check .` — fix with `ruff format <file>` if needed
> 3. `./venv/bin/pytest tests/ -q` — if failures, read test + implementation to fix
>
> ### Frontend
> 4. `cd frontend && npm run lint` — if ESLint errors, understand the rule and fix properly (no eslint-disable)
> 5. `cd frontend && npx tsc --noEmit` — fix type errors
> 6. `cd frontend && npx vitest run` — fix test failures
>
> After fixing ANY issue, re-run ALL checks from scratch. Up to 3 fix-and-verify cycles.
>
> Report your findings in this format:
> ```
> ## Review Results
> | Check | Status | Notes |
> |-------|--------|-------|
> | ruff check | ... | ... |
> | ruff format | ... | ... |
> | pytest | ... | ... |
> | eslint | ... | ... |
> | tsc | ... | ... |
> | vitest | ... | ... |
>
> ### Issues Fixed
> - ...
> ```

Wait for the reviewer to complete.

### 4b. Git commit and push
1. If on a shared/main branch, create a new branch: `git checkout -b feat/<change-name>`
2. Stage and commit with a descriptive message following existing commit style. End with `Co-Authored-By: Claude <noreply@anthropic.com>`.
3. If the reviewer fixed files, include them in the commit (or a separate `fix:` commit).
4. Push: `git push -u origin <branch-name>`

### 4c. Monitor CI
After pushing:
1. Wait 30 seconds, then check CI status: `gh pr checks <PR-number>` or `gh run list --branch <branch>`
2. If CI fails:
   - Read the failure logs: `gh run view <run-id> --log-failed`
   - Fix the issues locally
   - Commit and push the fix
   - Re-check CI (up to 2 retry cycles)

### 4d. Report

Print a summary table:

| Step | Status |
|------|--------|
| Change created | `<name>` |
| Architect artifacts | list of created artifacts |
| Tasks implemented | N/N |
| Reviewer | pass/fail + issues fixed |
| Tests | pass/fail (count) |
| CI | pass/fail |
| Committed | commit hash |
| Pushed to | branch name |
| Archived to | path |

List any files created or modified.

---

## Error Handling

- If `openspec new change` fails (name exists): append `-v2` suffix and retry
- If architect fails: fall back to developer-only mode (developer creates its own artifacts, like the old behavior)
- If developer hits an issue: try to fix it, if truly blocked skip the task and note it in the report
- If reviewer finds issues: fix them (up to 3 attempts), then report
- If CI fails after reviewer approval: read logs, fix, push, re-check (up to 2 attempts)
- Never stop the pipeline for a non-critical issue. Always produce a final report.
