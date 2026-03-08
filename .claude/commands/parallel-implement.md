# Parallel Implementation Pipeline

Explore multiple areas, pick the best improvement for each, and implement them all in parallel using the full OpenSpec lifecycle with specialized agents (architect designs, developer implements, reviewer validates).

**Input:** $ARGUMENTS — accepts two modes:

1. **Issue numbers** (recommended): `#85, #71, #63` — implement these specific GitHub Issues directly. Skips exploration and selection.
2. **Area names** (fallback): `Analytics, Deck Builder, Testing` — explores areas and picks the best items. Only use if no backlog issues exist.

**Typical workflow:**
```
/spec-backlog          →  see top 3 spec items
/product-backlog       →  see top 3 product ideas
/parallel-implement #85, #71, #63   →  implement those 3
```

**IMPORTANT:** Before running, ensure Read/Write/Bash/Glob/Grep permissions are set to "allow" — background agents cannot request permissions interactively. Worktree-isolated agents especially need Bash for CI verification and git operations.

---

## Phase 0: Parse input and fetch issue data

**If the user passed issue numbers** (e.g. `#85, #71, #63`):
- Fetch each issue:
  ```bash
  gh issue view {number} --json number,title,labels,body
  ```
- Extract from each issue body: area (from `area:*` label), value, effort, and feature details.
- For `spec-driven-backlog` issues: use "Missing deliverables" for the idea description, "Evidence of existing work" for context.
- For `product-driven-backlog` issues: use "Feature Description" for the idea description, "Implementation Notes" for context.
- **Skip Phase 1 and Phase 2** — go directly to confirmation table below.
- Present the issues to the user in a table:

  | # | Issue | Area | Value | Effort | Description |
  |---|-------|------|-------|--------|-------------|
  | 1 | #85 Price Trend Charts | Analytics | High | Low | ... |

  Wait for user confirmation. This is the **only interaction point**.

**If the user passed area names** (or nothing):
- Check both backlog types for open issues:
  ```bash
  gh issue list --label "spec-driven-backlog" --state open --limit 100 --json number,title,labels,body
  gh issue list --label "product-driven-backlog" --state open --limit 100 --json number,title,labels,body
  ```
- If backlog issues exist: filter by input areas, pick top 3 by value/effort ratio, present for confirmation.
- If no backlog issues exist: tell user to run `/update-spec-driven-backlog` or `/update-product-driven-backlog` first, then proceed to Phase 1.

---

## Phase 1: Explore (parallel)

**Only runs if Phase 0 found no backlog issues AND user passed area names.**

For each area, launch an **explorer** agent (`subagent_type: explorer`, `run_in_background: true`):
- Read relevant code, specs, and OpenSpec artifacts
- Identify what's built vs what's missing
- Generate improvement ideas with value/complexity ratings
- Prioritize by impact/effort ratio
- Write a summary to `.claude/agent-memory/product-ideation-explorer/<area>-exploration.md`

Wait for all explorers to complete. Read their output to extract findings.

## Phase 2: Select

**Only runs if Phase 1 ran (no backlog, area-based input).**

From each exploration, pick the single idea with the best impact/effort ratio.

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
>    - **tasks.md**: Atomic, ordered tasks with clear acceptance criteria. Each task specifies files involved, what "done" looks like, and dependencies on other tasks. Group by layer (Core -> Backend -> Frontend -> Tests). Include test tasks.
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

### 3a.1 Identify shared file conflicts

Before launching developers, scan all tasks.md files to identify **shared files** that multiple features will modify (common culprits: `client.ts`, `en.json`, `es.json`, `useApi.ts`, `App.tsx`).

For each shared file, decide:
- **Assign ownership**: Only ONE developer modifies it. Others document what they need in their tasks.md but skip the actual edit.
- **Or split cleanly**: If additions are independent (e.g., new interface + new method in client.ts), let each developer add their piece and the orchestrator merges.

Document the ownership plan before launching developers — this prevents manual merge headaches in Phase 4.

## Phase 3b: Implement (parallel, isolated worktrees)

### Pre-flight: Verify Bash permission

Before launching any developer agent, run a trivial Bash command (e.g. `echo "permission check"`) to confirm Bash is allowed. If it is NOT allowed:
- **Stop** and tell the user: "Bash permission is required for worktree developers to run CI and commit. Please set Bash to 'allow' and re-run."
- Do NOT launch developer agents without confirmed Bash permission — they will write code but cannot verify or commit it.

### Launch developers

For each change with completed artifacts, launch a **developer** agent in an isolated worktree (`subagent_type: developer`, `isolation: worktree`, `run_in_background: true`).

**CRITICAL:** Read the full content of each architect's `tasks.md` and inline it directly into the developer's prompt. Do NOT just tell the developer to "read tasks.md" — past sprints showed that developers who must discover their own tasks sometimes misidentify or skip them.

Each agent's prompt should be:

> You are implementing a feature that has already been designed by an architect. The OpenSpec change artifacts are ready — your job is to execute the implementation.
>
> **Change name:** "<name>"
>
> ## Tasks to implement
>
> <PASTE THE FULL CONTENT OF tasks.md HERE — every task, every acceptance criterion, every file path>
>
> Execute the implementation phase without any user interaction:
>
> 1. **Read context files**: Read the design at `openspec/changes/<name>/design.md` and every file referenced in the tasks below. Understand the codebase before writing code.
> 2. **Implement**: Follow the tasks above in order. For each task:
>    - Read the acceptance criteria carefully
>    - Implement the change following the design's architectural decisions
>    - Mark the task as done: `- [ ]` -> `- [x]`
> 4. **Verify** with the full CI-equivalent suite:
>    - `ruff check .` (fix with `--fix` if needed)
>    - `ruff format --check .` (fix with `ruff format <file>` if needed)
>    - `./venv/bin/pytest tests/ -q`
>    - `cd frontend && npm run lint` (NOT just tsc — this catches ESLint rules like react-hooks)
>    - `cd frontend && npx tsc --noEmit`
>    - `cd frontend && npx vitest run`
>    Fix failures (up to 3 attempts).
> 5. **Commit your changes**: `git add -A && git commit -m "feat: <change-name>"` — this makes merge easier. Do NOT add `Co-Authored-By` trailers.
> 6. **Do NOT archive** — the orchestrator handles archival after merge.
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
> - If a task is unclear, refer back to design.md for the architectural decision.
> - **Shared files**: <list any shared file ownership rules from step 3a.1 here>

Wait for all developers to complete.

### Post-flight: Validate worktree diffs

After all developers complete, for each worktree:
1. Run `git status --short` and `git diff main..HEAD --name-only` (or `git diff HEAD --name-only` if uncommitted).
2. Extract the list of files that **should** have been modified from the architect's tasks.md.
3. **Compare**: If the worktree diff does NOT include the expected files, mark that developer as **FAILED** immediately.
4. Failed developers' tasks will be reassigned to the reviewer in Phase 4b.

This prevents discovering failures late during the merge phase.

## Phase 4: Merge & Review

**This phase is fully autonomous — do NOT ask the user for confirmation at any step.**

### 4a. Merge worktree changes to main repo

For each completed worktree:
1. **Get the diff**: `cd <worktree> && git diff HEAD --name-only` to identify changed files (developers should have committed, so use `git diff main..HEAD --name-only` if committed).
2. **Copy feature-specific files**: Only copy files unique to this feature. Skip shared files (client.ts, en.json, es.json) — merge those manually.
3. **Merge shared files**: For files modified by multiple developers, read each version, identify the additions, and splice them into the main repo's version. Never blindly overwrite.
4. **Clean up**: `git worktree remove --force <worktree>`

### 4b. Launch Reviewer agent

Launch a single **reviewer** agent (`subagent_type: reviewer`) to validate ALL merged changes together.

The reviewer's prompt should be:

> You are the final quality gate. All developer agents have completed and their changes have been merged into the main repo. Your job is to run the exact CI/CD pipeline checks and fix any issues.
>
> **Features implemented:** <list the features and their change names>
>
> **Files changed:** <list all modified/created files across all features>
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
> After fixing ANY issue, re-run ALL checks from scratch (a fix in one area can break another). Up to 3 fix-and-verify cycles.
>
> Also review for cross-feature merge issues:
> - Duplicate imports or type definitions from parallel developers
> - Conflicting changes to shared files (en.json, es.json, client.ts, useApi.ts)
> - Inconsistent patterns between features
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
>
> ### Files Modified by Reviewer
> - ...
> ```

Wait for the reviewer to complete. Read its report.

### 4c. Git commit, push, and PR
1. Create a **new branch** from `main`: `git checkout main && git pull && git checkout -b feat/<descriptive-name>`
2. Copy/apply all changes onto this branch (stash + pop if needed).
3. Create **one commit per feature** with descriptive messages following existing commit style (e.g., `fix:`, `feat:`, `test:`, `refactor:`). Do NOT add `Co-Authored-By` trailers.
4. If the reviewer modified files, create an additional commit: `fix: resolve CI issues (reviewer)`.
5. Push the branch: `git push -u origin <branch-name>`
6. **Link backlog issues to the PR** — If any implemented features originated from backlog issues (Phase 0/2), include `Closes #XX` in the PR body for each resolved issue. This ensures GitHub automatically closes the issues when the PR is merged.
   ```
   gh pr create --title "feat: ..." --body "$(cat <<'EOF'
   ## Summary
   - ...

   ## Closes
   Closes #85, Closes #71, Closes #63

   ## Test plan
   - ...
   EOF
   )"
   ```
   **Rules for linking issues:**
   - Only link issues that are **fully resolved** by this PR (all missing deliverables implemented).
   - If a feature only partially addresses an issue, do NOT close it — instead add a comment on the issue noting progress:
     ```bash
     gh issue comment {number} --body "Partial progress in PR #{pr_number}: {what was done}. Remaining: {what's left}."
     ```
   - For `spec-driven-backlog` issues: check that ALL missing deliverables listed in the issue are now implemented.
   - For `product-driven-backlog` issues: the feature described in the issue should be fully functional.

### 4d. Monitor CI
After pushing:
1. Wait 30 seconds, then check CI status: `gh pr checks <PR-number>`
2. If CI fails:
   - Read the failure logs: `gh run view <run-id> --log-failed`
   - Fix the issues locally
   - Commit and push the fix
   - Re-check CI (up to 2 retry cycles)
3. Include final CI status in the report.

### 4e. Report
Produce a summary table:

| Area | Feature | Change Name | Architect | Developer | Reviewer | Tests | CI | Status |
|------|---------|-------------|-----------|-----------|----------|-------|----|--------|

List files created or modified per area. Include the PR URL and CI status.

---

## Error Handling

- If an explorer fails: skip that area, continue with others
- If an architect fails: skip that area, report the failure. Suggest running `/auto-implement <description>` manually.
- If a developer fails mid-pipeline: report which phase it failed at and the error. Suggest running `/auto-implement <description>` manually for that feature.
- If the reviewer finds unfixable issues: report them clearly, push what works, note failures in the PR description.
- If CI fails after reviewer approval: attempt to fix (read `gh run view --log-failed`), push fix, re-check.
- Never block the entire pipeline on a single agent failure. Always produce a final report.
