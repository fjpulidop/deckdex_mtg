# Parallel Implementation Pipeline

Explore multiple areas, pick the best improvement for each, and implement them all in parallel using the full OpenSpec lifecycle.

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

## Phase 3: Auto-Implement (parallel, isolated)

For each chosen idea, launch a **developer** agent in an isolated worktree (`isolation: worktree`, `run_in_background: true`).

Each agent's prompt should be:

> You are implementing a feature autonomously. Follow the `/auto-implement` command workflow exactly.
>
> **Description:** "<one-line description of the chosen idea>"
>
> Execute the full OpenSpec lifecycle without any user interaction:
>
> 1. **Setup**: Derive a kebab-case change name from the description.
> 2. **Fast-Forward**: Use the `openspec-ff-change` skill to create all artifacts. Run `openspec new change "<name>"`, then loop through artifacts using `openspec status --json` and `openspec instructions --json`. Create proposal, design, delta-spec, and tasks grounded in actual codebase patterns.
> 3. **Implement**: Use the `openspec-apply-change` skill. Get apply instructions via `openspec instructions apply --json`, read context files, implement each task, mark `- [ ]` -> `- [x]`.
> 4. **Verify**: Run `cd frontend && npx tsc --noEmit` and `./venv/bin/pytest tests/ -q`. Fix failures (up to 3 attempts).
> 5. **Archive**: Use the `openspec-archive-change` skill. Sync delta specs, then move to `openspec/changes/archive/`.
>
> **Rules:**
> - Never ask for clarification. Make reasonable decisions and keep moving.
> - Follow existing codebase patterns (check similar files before writing new ones).
> - Backend: thin routes, services for logic, Pydantic models.
> - Frontend: functional components, TanStack Query, Tailwind, strict TypeScript, i18n in en.json + es.json.
> - Tests: pytest functions in `tests/`, mock external deps, use `dependency_overrides` with setUp/tearDown per class (NOT module-level).
> - Use `openspec` CLI commands throughout — this is non-negotiable.

Wait for all agents to complete.

## Phase 4: Report

After all agents finish, produce a summary table:

| Area | Feature | Change Name | Artifacts | Tasks | Tests | Archived | Status |
|------|---------|-------------|-----------|-------|-------|----------|--------|

Then run final verification on the merged result:
1. TypeScript compiles: `cd frontend && npx tsc --noEmit`
2. All tests pass: `./venv/bin/pytest tests/ -q`
3. List any files created or modified per area

If any verification fails post-merge, fix the conflicts and report what was adjusted.

---

## Error Handling

- If an explorer fails: skip that area, continue with others
- If an auto-implement agent fails mid-pipeline: report which phase it failed at and the error. Suggest running `/auto-implement <description>` manually for that feature.
- If post-merge verification fails: attempt to fix (likely test isolation issues like module-level overrides), report fixes made
- Never block the entire pipeline on a single agent failure. Always produce a final report.
