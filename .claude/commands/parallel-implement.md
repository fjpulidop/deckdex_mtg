# Parallel Implementation Pipeline

Explore multiple areas, pick the best improvement for each, and implement them all in parallel using the full OpenSpec lifecycle with specialized agents (architect designs, developer implements).

**Input:** $ARGUMENTS (comma-separated areas, e.g. "Analytics, Deck Builder, Testing")

**IMPORTANT:** Before running, ensure Read/Write/Bash/Glob/Grep permissions are set to "allow" — background agents cannot request permissions interactively.

---

## Phase 1: Explore (parallel)

For each area, launch an **explorer** agent (`subagent_type: explorer`, `run_in_background: true`):
- Read relevant code, specs, and OpenSpec artifacts
- Identify what's built vs what's missing
- Generate improvement ideas with value/complexity ratings
- Prioritize by impact/effort ratio
- Write a summary to `.claude/agent-memory/product-ideation-explorer/<area>-exploration.md`

Wait for all explorers to complete. Read their output to extract findings.

## Phase 2: Select

From each exploration, **pick the single idea with the best impact/effort ratio**.

Present the chosen ideas to the user in a table:

| Area | Idea | Rationale | Estimated Complexity |
|------|------|-----------|---------------------|

Wait for user confirmation before proceeding. This is the **only interaction point** — everything after this is fully autonomous.

## Phase 3a: Architect (parallel, in main repo)

For each chosen idea, launch an **architect** agent (`subagent_type: architect`, `run_in_background: true`).

Each architect creates OpenSpec artifacts in `openspec/changes/<name>/`. Since each change writes to its own directory, multiple architects can run in parallel without conflicts.

Each agent's prompt should be:

> You are designing a feature autonomously. Create high-quality OpenSpec artifacts.
>
> **Description:** "<one-line description of the chosen idea>"
>
> **Context from exploration:** <paste key findings from the explorer for this area>
>
> Execute the OpenSpec design phase without any user interaction:
>
> 1. **Setup**: Derive a kebab-case change name from the description.
> 2. **Create change**: Run `openspec new change "<name>"`.
> 3. **Read codebase**: Before writing any artifact, read the actual code files involved. Read relevant specs from `openspec/specs/`. Read layer-specific CLAUDE.md files and `.claude/rules/`. Understand existing patterns.
> 4. **Create artifacts** using `openspec status --json` and `openspec instructions --json` to loop through each required artifact:
>    - **proposal.md**: What and why. Product motivation, scope, success criteria.
>    - **design.md**: Detailed technical design. Reference actual file paths, existing patterns, real code structures. Include impact analysis (which files/modules/APIs change), architectural decisions with rationale, data flow diagrams where helpful, and risks/edge cases.
>    - **delta-spec**: Only sections that change from existing specs. Reference the base spec.
>    - **tasks.md**: Atomic, ordered tasks with clear acceptance criteria. Each task specifies files involved, what "done" looks like, and dependencies on other tasks. Group by layer (Core → Backend → Frontend → Tests). Include test tasks.
>
> **Quality standards:**
> - Every artifact must reference real file paths and existing code patterns (not theoretical)
> - Design decisions must be justified (why this approach over alternatives)
> - Tasks must be implementable by a developer who hasn't seen the exploration — they should be self-contained
> - Include edge cases, error handling requirements, and migration needs in the design
>
> **Rules:**
> - Never ask for clarification. Make reasonable decisions and document your choices.
> - Read code before writing artifacts — ground everything in the actual codebase.
> - Use `openspec` CLI commands throughout — this is non-negotiable.

Wait for all architects to complete. Briefly review their output to confirm artifacts were created.

## Phase 3b: Implement (parallel, isolated worktrees)

For each change with completed artifacts, launch a **developer** agent in an isolated worktree (`subagent_type: developer`, `isolation: worktree`, `run_in_background: true`).

Each agent's prompt should be:

> You are implementing a feature that has already been designed by an architect. The OpenSpec change artifacts are ready — your job is to execute the implementation.
>
> **Change name:** "<name>"
>
> Execute the implementation phase without any user interaction:
>
> 1. **Read the architect's artifacts**: Read all files in `openspec/changes/<name>/` — proposal.md, design.md, delta-spec, tasks.md. These are your blueprint.
> 2. **Read context files**: Read every file referenced in the design and tasks. Understand the codebase before writing code.
> 3. **Implement**: Follow tasks.md in order. For each task:
>    - Read the acceptance criteria carefully
>    - Implement the change following the design's architectural decisions
>    - Mark the task as done: `- [ ]` -> `- [x]`
> 4. **Verify**: Run ALL checks — `ruff check .` (fix with `--fix` if needed), `cd frontend && npx tsc --noEmit`, `./venv/bin/pytest tests/ -q`, and `cd frontend && npx vitest run`. Fix failures (up to 3 attempts).
> 5. **Archive**: Run `openspec sync-specs` then `openspec archive change "<name>"`.
>
> **Rules:**
> - Never ask for clarification. The architect's artifacts have your answers.
> - Follow existing codebase patterns (check similar files before writing new ones).
> - Backend: thin routes, services for logic, Pydantic models.
> - Frontend: functional components, TanStack Query, Tailwind, strict TypeScript, i18n in en.json + es.json.
> - Tests: pytest functions in `tests/`, mock external deps, use `dependency_overrides` with setUp/tearDown per class (NOT module-level).
> - Use `openspec` CLI commands throughout — this is non-negotiable.
> - If a task is unclear, refer back to design.md for the architectural decision.

Wait for all developers to complete.

## Phase 4: Merge, Verify & Ship

**This phase is fully autonomous — do NOT ask the user for confirmation at any step.**

### 4a. Copy worktree changes to main repo
For each completed worktree, copy modified/new files back to the main repo. Then clean up worktrees with `git worktree remove`.

### 4b. Verify merged result (must pass ALL checks)
1. Linting: `ruff check .` (fix with `ruff check . --fix` if needed)
2. TypeScript compiles: `cd frontend && npx tsc --noEmit`
3. Backend tests pass: `./venv/bin/pytest tests/ -q`
4. Frontend tests pass: `cd frontend && npx vitest run`
5. If any verification fails, fix and re-verify (up to 3 attempts).

### 4c. Git commit, push, and PR
1. Create a **new branch** from `main`: `git checkout main && git pull && git checkout -b feat/<descriptive-name>`
2. Copy/apply all changes onto this branch (stash + pop if needed).
3. Create **one commit per feature** with descriptive messages following existing commit style (e.g., `fix:`, `feat:`, `test:`, `refactor:`). End each message with `Co-Authored-By: Claude <noreply@anthropic.com>`.
4. Push the branch: `git push -u origin <branch-name>`
5. Create a PR with `gh pr create` summarizing all features, linking each commit.

### 4d. Report
Produce a summary table:

| Area | Feature | Change Name | Architect | Developer | Tests | Archived | Status |
|------|---------|-------------|-----------|-----------|-------|----------|--------|

List files created or modified per area. Include the PR URL.

---

## Error Handling

- If an explorer fails: skip that area, continue with others
- If an architect fails: skip that area, report the failure. Suggest running `/auto-implement <description>` manually.
- If a developer fails mid-pipeline: report which phase it failed at and the error. Suggest running `/auto-implement <description>` manually for that feature.
- If post-merge verification fails: attempt to fix (likely test isolation issues like module-level overrides), report fixes made
- Never block the entire pipeline on a single agent failure. Always produce a final report.
