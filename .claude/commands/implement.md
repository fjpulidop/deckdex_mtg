# Implementation Pipeline

Full OpenSpec lifecycle with specialized agents: architect designs, developer implements, reviewer validates and archives. Handles 1 to N features — adapts automatically (sequential for 1, parallel with worktrees for N).

**MANDATORY: Always follow this pipeline exactly as written. NEVER skip, shortcut, or "optimize away" any phase — even if the task seems simple enough to do directly. The orchestrator MUST launch the architect, developer, and reviewer agents as specified. Do NOT implement changes yourself in the main conversation; delegate to the agents defined in each phase. No exceptions.**

**Input:** $ARGUMENTS — accepts three modes:

1. **Issue numbers** (recommended): `#85, #71, #63` — implement these specific GitHub Issues directly. Skips exploration and selection.
2. **Text description** (single feature): `"add price history chart to analytics"` — implement a single feature from a description. Skips exploration and selection.
3. **Area names** (fallback): `Analytics, Deck Builder, Testing` — explores areas and picks the best items. Only use if no backlog issues exist.

**Typical workflow:**
```
/spec-backlog          →  see top 3 spec items
/product-backlog       →  see top 3 product ideas
/implement #85, #71, #63   →  implement those 3
/implement "add price history chart"  →  implement one feature
```

**IMPORTANT:** Before running, ensure Read/Write/Bash/Glob/Grep permissions are set to "allow" — background agents cannot request permissions interactively. Worktree-isolated agents especially need Bash for CI verification and git operations.

---

## Phase -1: Environment Setup (cloud pre-flight)

**This phase runs BEFORE anything else.** Detect if we're in a cloud/remote environment and ensure all required tools are available.

### Detection

Check the environment variable `CLAUDE_CODE_ENTRYPOINT`. If it contains `remote_mobile` or `remote_web`, OR if `CLAUDE_CODE_REMOTE` is `true`, we're in a **cloud environment** and must verify the toolchain.

```bash
if [ "$CLAUDE_CODE_REMOTE" = "true" ] || [[ "$CLAUDE_CODE_ENTRYPOINT" == remote_* ]]; then
  echo "CLOUD_ENV=true"
fi
```

### Checks to run (sequential, fail-fast)

Run each check. If a tool is missing, install/configure it before proceeding. Report a summary table at the end.

#### 1. GitHub CLI authentication

```bash
gh auth status 2>&1
```

- If `gh` is not authenticated: The local git proxy handles `git push/pull` but `gh` CLI needs separate auth for API calls (issues, PRs, checks).
- **Fix**: Check if the git remote uses a local proxy (`127.0.0.1`). If so, try to configure `gh` to work with it. If that fails, **warn the user** that PR creation and issue operations will not work, but continue — the pipeline can still architect, develop, and commit. PR creation will be skipped in Phase 4c.
- Set `GH_AVAILABLE=true/false` for later phases.

#### 2. OpenSpec CLI

```bash
which openspec && openspec --version
```

- If missing: `npm install -g @openspec/cli` (or check if it's in `node_modules/.bin/openspec`).
- If install fails: **STOP** — openspec is required for the architect phase. Tell the user: "OpenSpec CLI is required. Install it with `npm install -g @openspec/cli`."

#### 3. Python dependencies (backend)

```bash
python3 -c "import fastapi, httpx, slowapi, loguru, pydantic, sqlalchemy, ruff" 2>&1
```

- If any import fails: `pip install -r requirements.txt -r backend/requirements-api.txt -q`
- Also verify `ruff` and `pytest` are in PATH: `which ruff pytest`
- If `pytest` is not available as a command, note to use `python3 -m pytest` instead in all CI commands.

#### 4. Frontend dependencies

```bash
[ -d frontend/node_modules ] && echo "OK" || echo "MISSING"
```

- If missing: `cd frontend && npm install`

#### 5. Python virtual environment

```bash
[ -f venv/bin/python ] && echo "OK" || echo "MISSING"
```

- If `venv/` doesn't exist but `python3 -m pytest` works, that's fine — just note that CI commands should use `python3 -m pytest` instead of `./venv/bin/pytest`.
- Set `PYTEST_CMD` to either `./venv/bin/pytest tests/ -q` or `python3 -m pytest tests/ -q` accordingly.

### Summary

Print a setup report:

```
## Environment Setup
| Tool | Status | Notes |
|------|--------|-------|
| GitHub CLI | ✓ / ✗ | authenticated / PR creation disabled |
| OpenSpec | ✓ v1.2.0 | |
| Python deps | ✓ | |
| Frontend deps | ✓ | |
| pytest | ✓ | via python3 -m pytest |
```

If any **critical** tool is missing (OpenSpec, Python deps), stop and tell the user. If only `gh` auth is missing, continue with `GH_AVAILABLE=false` — skip PR creation in Phase 4c and tell the user to create the PR manually.

**Pass `PYTEST_CMD` and `GH_AVAILABLE` forward** — all later phases must use these instead of hardcoded commands.

---

## Phase 0: Parse input and determine mode

**If the user passed a text description** (e.g. `"add price history chart"`):
- This is a **single-feature mode**. Derive a kebab-case change name from the description.
- Set `SINGLE_MODE = true`. No worktrees, no parallelism — everything runs sequentially in the main repo.
- **Skip Phase 1 and Phase 2** — go directly to Phase 3a.

**If the user passed issue numbers** (e.g. `#85, #71, #63`):
- Fetch each issue:
  ```bash
  gh issue view {number} --json number,title,labels,body
  ```
- Extract from each issue body: area (from `area:*` label), value, effort, and feature details.
- For `spec-driven-backlog` issues: use "Missing deliverables" for the idea description, "Evidence of existing work" for context.
- For `product-driven-backlog` issues: use "Feature Description" for the idea description, "Implementation Notes" for context.
- If only 1 issue: set `SINGLE_MODE = true`.
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

For each area, launch a **product-manager** agent (`subagent_type: product-manager`, `run_in_background: true`):
- Read relevant code, specs, and OpenSpec artifacts
- Identify what's built vs what's missing
- Generate improvement ideas with value/complexity ratings
- Prioritize by impact/effort ratio
- Write a summary to `.claude/agent-memory/product-ideation-explorer/<area>-exploration.md`

Wait for all product-managers to complete. Read their output to extract findings.

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
> **Context from exploration:** <paste key findings from the product-manager for this area>
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
>    - **tasks.md**: Atomic, ordered tasks with clear acceptance criteria. Each task specifies files involved, what "done" looks like, and dependencies on other tasks. Group by layer (Core -> Backend -> Frontend -> Tests). Include test tasks. Tag each task with its layer: `[backend]`, `[frontend]`, `[core]`, or `[test]`.
>    - **context-bundle.md**: A compact reference for the developer. For each file that will be modified or is critical context, include:
>      - File path
>      - Key patterns used (e.g., "uses Repository pattern", "exports via client.ts")
>      - Relevant existing code snippets (imports, function signatures, type definitions) — just enough to implement without re-reading the full file
>      - Dependencies and imports the developer will need
>      This saves the developer from re-reading every referenced file. Keep it under 200 lines.
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

### 3a.2 Pre-validate architect output

Before launching developers, quick-check each architect's artifacts:

1. **tasks.md exists** and has at least one task with `- [ ]`
2. **context-bundle.md exists** (the developer depends on it)
3. **File references are real**: Extract all file paths from tasks.md, run `ls` on each. If >30% don't exist, the architect hallucinated — mark it as FAILED and skip this feature.
4. **Layer tags present**: Each task should have `[backend]`, `[frontend]`, `[core]`, or `[test]`. If missing, assign them based on file paths (e.g., `frontend/` → `[frontend]`, `tests/` → `[test]`).

This catches architect failures early, before wasting developer tokens on bad blueprints.

## Phase 3b: Implement

### Pre-flight: Verify Bash permission

Before launching any developer agent, run a trivial Bash command (e.g. `echo "permission check"`) to confirm Bash is allowed. If it is NOT allowed:
- **Stop** and tell the user: "Bash permission is required for developers to run CI and commit. Please set Bash to 'allow' and re-run."
- Do NOT launch developer agents without confirmed Bash permission — they will write code but cannot verify or commit it.

### Launch developers

**CRITICAL:** Read the full content of each architect's `tasks.md` and `context-bundle.md` and inline them directly into the developer's prompt. Do NOT just tell the developer to "read tasks.md" — past sprints showed that developers who must discover their own tasks sometimes misidentify or skip them.

**Read reviewer learnings:** Before building the developer prompt, check if `.claude/agent-memory/reviewer/common-fixes.md` exists. If it does, read it and include its content in the developer prompt as "lessons from past reviews" — this prevents developers from repeating mistakes the reviewer has already caught.

#### Choosing the right developer agent

For each feature, analyze the tasks' layer tags to decide which developer(s) to launch:

- **All `[backend]`/`[core]`/`[test]` tasks**: Use `backend-developer` (lighter prompt, backend-only CI)
- **All `[frontend]`/`[test]` tasks**: Use `frontend-developer` (lighter prompt, frontend-only CI)
- **Mixed layers**: Use the generic `developer` (full-stack prompt, full CI)

This reduces token usage — a backend-only feature doesn't need React/TypeScript/Tailwind rules in its prompt.

#### Launch modes

**If `SINGLE_MODE`**: Launch the appropriate developer agent in the main repo. No worktree, no background — run in foreground.

**If multiple features**: For each change, launch the appropriate developer agent in an isolated worktree (`isolation: worktree`, `run_in_background: true`).

#### Developer prompt template

Each agent's prompt should be:

> You are implementing a feature that has already been designed by an architect. The OpenSpec change artifacts are ready — your job is to execute the implementation.
>
> **Change name:** "<name>"
>
> ## Context bundle
>
> <PASTE THE FULL CONTENT OF context-bundle.md HERE — key patterns, snippets, imports from relevant files. Use this instead of re-reading every file from scratch. Only read a file fully if the bundle doesn't cover what you need.>
>
> ## Tasks to implement
>
> <PASTE THE FULL CONTENT OF tasks.md HERE — every task, every acceptance criterion, every file path>
>
> ## Lessons from past reviews
>
> <IF `.claude/agent-memory/reviewer/common-fixes.md` EXISTS, PASTE ITS CONTENT HERE. Otherwise write "No reviewer learnings yet.">
>
> Execute the implementation phase without any user interaction:
>
> 1. **Read context**: Use the context bundle above as your primary reference. Only read full files when the bundle doesn't cover what you need. Read `openspec/changes/<name>/design.md` for architectural decisions.
> 2. **Implement**: Follow the tasks above in order. For each task:
>    - Read the acceptance criteria carefully
>    - Implement the change following the design's architectural decisions
>    - Mark the task as done: `- [ ]` -> `- [x]`
> 3. **Verify** with CI checks (run only the checks relevant to your layer):
>    - Backend: `ruff check .` → `ruff format --check .` → `{PYTEST_CMD}` (from Phase -1 setup)
>    - Frontend: `cd frontend && npm run lint` → `npx tsc --noEmit` → `npx vitest run`
>    Fix failures (up to 3 attempts).
> 4. **Commit your changes**: `git add -A && git commit -m "feat: <change-name>"` — this makes merge easier. Do NOT add `Co-Authored-By` trailers.
> 5. **Do NOT archive** — the reviewer agent handles archival after CI validation.
>
> **Rules:**
> - Never ask for clarification. The architect's artifacts have your answers.
> - Follow existing codebase patterns (check similar files before writing new ones).
> - Pay attention to the "Lessons from past reviews" section — these are real mistakes from previous sprints.
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

**If `SINGLE_MODE`**: Skip this step — the developer already worked in the main repo.

**If multiple features**: For each completed worktree:
1. **Get the diff**: `cd <worktree> && git diff HEAD --name-only` to identify changed files (developers should have committed, so use `git diff main..HEAD --name-only` if committed).
2. **Copy feature-specific files**: Only copy files unique to this feature. Skip shared files (client.ts, en.json, es.json) — merge those manually.
3. **Merge shared files**: For files modified by multiple developers, read each version, identify the additions, and splice them into the main repo's version. Never blindly overwrite.
4. **Clean up**: `git worktree remove --force <worktree>`

### 4b. Launch Reviewer agent

Launch a single **reviewer** agent (`subagent_type: reviewer`) to validate ALL merged changes together.

The reviewer's prompt should be:

> You are the final quality gate. All developer agents have completed and their changes have been merged into the main repo. Your job is to run the exact CI/CD pipeline checks, fix any issues, and archive the completed changes.
>
> **Features implemented:** <list the features and their change names>
>
> **Files changed:** <list all modified/created files across all features>
>
> ## Step 1: CI Verification
>
> Run the full CI-equivalent verification suite in this exact order:
>
> ### Backend
> 1. `ruff check .` — fix with `ruff check . --fix` if needed
> 2. `ruff format --check .` — fix with `ruff format <file>` if needed
> 3. `{PYTEST_CMD}` (use the command determined in Phase -1; typically `python3 -m pytest tests/ -q` in cloud or `./venv/bin/pytest tests/ -q` locally) — if failures, read test + implementation to fix
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
> ## Step 2: Record learnings
>
> If you fixed ANY issues, append a summary to `.claude/agent-memory/reviewer/common-fixes.md`. Format:
> ```
> ## Sprint {DATE}
> - {description of fix}: {what was wrong} -> {how you fixed it}
> ```
> Keep entries concise (1 line each). This file is read by future developers to avoid repeating mistakes. If the file already has >50 entries, remove the oldest 10.
>
> ## Step 3: Archive changes
>
> After ALL checks pass, archive each completed change:
> ```bash
> openspec sync-specs "<change-name>"
> openspec archive change "<change-name>"
> ```
> Repeat for each change name listed above.
>
> ## Report
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
>
> ### Archived Changes
> - ...
> ```

Wait for the reviewer to complete. Read its report.

### 4c. Git commit, push, and PR
1. Create a **new branch** from `main`: `git checkout main && git pull && git checkout -b feat/<descriptive-name>`
2. Copy/apply all changes onto this branch (stash + pop if needed).
3. Create **one commit per feature** with descriptive messages following existing commit style (e.g., `fix:`, `feat:`, `test:`, `refactor:`). Do NOT add `Co-Authored-By` trailers.
4. If the reviewer modified files, create an additional commit: `fix: resolve CI issues (reviewer)`.
5. Push the branch: `git push -u origin <branch-name>`
6. **If `GH_AVAILABLE=false`** (from Phase -1): Skip PR creation. Instead, print the compare URL for the user to create the PR manually:
   ```
   PR creation skipped (GitHub CLI not authenticated).
   Create the PR manually at: https://github.com/{owner}/{repo}/compare/main...<branch-name>
   ```
   Then skip to Phase 4e (Report).
7. **Link backlog issues to the PR** — If any implemented features originated from backlog issues (Phase 0/2), include `Closes #XX` in the PR body for each resolved issue. This ensures GitHub automatically closes the issues when the PR is merged.
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

- If a product-manager fails: skip that area, continue with others
- If an architect fails: skip that area, report the failure. Suggest running `/implement "<description>"` manually for that feature.
- If a developer fails mid-pipeline: report which phase it failed at and the error. Suggest running `/implement "<description>"` manually for that feature.
- If the reviewer finds unfixable issues: report them clearly, push what works, note failures in the PR description.
- If CI fails after reviewer approval: attempt to fix (read `gh run view --log-failed`), push fix, re-check.
- Never block the entire pipeline on a single agent failure. Always produce a final report.
