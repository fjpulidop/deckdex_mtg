---
name: /git-flow
id: git-flow
category: Git
description: Complete git workflow - add, commit, push, and create PR (always branch from main)
---

Execute the complete git workflow: stage changes, create commit (on a branch from main), push, and open a pull request.

**Input**: Optional custom commit message or branch name

**Steps**

This command orchestrates the full git workflow. **Rule: New work always lands on a feature branch created from an up-to-date main; never commit directly to main.**

1. **Stage all changes** (`/git-add`)
   ```bash
   git add -A
   git status --short
   ```
   Show what files are being staged. If nothing to commit, stop and inform the user.

2. **Generate commit message** (do not commit yet)
   - Analyze staged diff and recent commit style (`git diff --cached`, `git log -5 --oneline`).
   - Generate message in conventional commits format (feat, fix, docs, refactor, test, chore, perf, style).
   - Show generated message to user; prompt: **Use this message? [Yes/Edit/Cancel]**.
   - If Edit: let user provide custom message. Store the **approved message** for the next steps.

3. **Ensure work is on a branch from main** (SMART BRANCH LOGIC)
   
   **a. Get current branch**
   ```bash
   git branch --show-current
   ```
   
   **b. If current branch is main (or master):**
   - Do **not** commit on main.
   - Stash changes (including staged):
     ```bash
     git stash push -u -m "git-flow: staged and unstaged"
     ```
   - Update main and create a new branch from it:
     ```bash
     git checkout main
     git pull
     ```
   - Derive **branch name** from the approved commit message first line:
     - Conventional form `type(scope): subject` or `type: subject` → branch `type/slug`.
     - Slug: lowercase, replace spaces and punctuation with one hyphen, drop redundant words (e.g. "to reduce token usage" → keep "compact-specs" from subject/scope). Prefer scope or first 2–3 meaningful words of subject.
     - Examples: `docs(openspec): compact specs` → `docs/openspec-compact-specs`; `feat: add CLI options` → `feat/add-cli-options`; `fix: dashboard bugs` → `fix/dashboard-bugs`.
   - Create and switch to the new branch:
     ```bash
     git checkout -b <derived-branch-name>
     ```
   - Restore changes and commit on the new branch:
     ```bash
     git stash pop
     git add -A
     git commit -m "<approved message>"
     ```
   - Continue to step 4 (Push).
   
   **c. If current branch is a feature branch (not main):**
   - Option A — **Use current branch**: Commit with the approved message on this branch, then push. Continue to step 4.
   - Option B — **Re-branch from main** (when changes clearly belong to a different scope than the current branch name): Offer the user: "Current branch is `<name>`. Create a new branch from main for this work?" If yes, same flow as 3b: stash → checkout main → pull → new branch from message → stash pop → add → commit. Then continue to step 4.
   - Prefer Option A unless the user previously asked to "always branch from main" or the change set is obviously unrelated (e.g. only `openspec/` changes while on `fix/web-dashboard-bugs`); then offer Option B.

4. **Push to remote** (`/git-push`)
   - If new branch: `git push -u origin <branch-name>`.
   - If existing branch: `git push`.
   - Show branch name, remote, and number of commits pushed.

5. **Check if PR needed** (SMART PR LOGIC — prefer `gh`, fallback to manual URL)
   - **First:** Check if GitHub CLI is available (`gh --version` or `command -v gh`). If **yes**, use `gh` for all PR steps below. If **no**, skip `gh` and go directly to fallback.
   - **With `gh` available:**
     - List PR for current branch: `gh pr list --head <branch-name> --json number,url,title`.
     - **If PR exists:** Skip creation; show existing PR URL and note that new commits were added.
     - **If no PR:** Generate description from commits and diff vs main, then `gh pr create --title "..." --body "..."`.
   - **Without `gh` (or if `gh` fails):** Do not fail. Show manual PR URL: `https://github.com/<owner>/<repo>/compare/main...<branch-name>` and suggest installing `gh` for next time.

6. **Show complete summary** (what was staged, commit hash and message, branch, push result, PR link or manual PR URL).

**Checkpoints**

At each step, show progress and allow user to:
- Continue to next step
- Skip remaining steps
- Cancel workflow

**Output On Complete Success (PR Created)**

```
## Git Workflow Complete ✅

### 1. Files Staged
- 23 files staged (5 new, 15 modified, 3 deleted)

### 2. Commit Created
- Commit: abc1234
- Message: feat: enhance CLI with configuration options
- Branch: feat/enhance-cli (created from main)
- Files: 23 changed (+2,525, -228)

### 3. Pushed to Remote
- Branch: feat/enhance-cli
- Remote: origin/feat/enhance-cli
- Commits pushed: 1

### 4. Pull Request Created
- PR #42: feat: Enhanced CLI with configuration options
- URL: https://github.com/user/repo/pull/42
- Status: Ready for review

---

**Next steps:** View PR, assign reviewers, wait for CI.
```

**Output On Complete Success (PR Already Exists)**

```
## Git Workflow Complete ✅

### 4. Pull Request
- ℹ️  PR already exists for this branch
- PR #5: feat: Incremental Price Updates
- URL: https://github.com/user/repo/pull/5
- New commits have been added to the existing PR
```

**Output On Partial Success**

```
## Git Workflow Partial Complete

✅ Completed: 1. Staged  2. Commit (branch from main)  3. Pushed
⏸️ Stopped at: 4. Pull Request (user chose to create manually)

Create PR manually: https://github.com/owner/repo/compare/main...feat/branch-name
Or run `/git-pr` later.
```

**Guardrails**

- **Never commit to main** in this workflow: when on main, always create a branch from an up-to-date main first, then commit on that branch.
- **Always base new branches on main:** after `git checkout main`, run `git pull` before `git checkout -b <name>`.
- Stop on any errors and show a clear message.
- Allow user to cancel at any step; show what was completed and what remains.
- Show progress clearly (e.g. [1/5] … [5/5]).
- **Branch naming:** derive from approved commit message; keep type (feat/fix/docs/etc.) and a short slug; user can override if they provide a branch name as input.
- **PR:** Prefer `gh` when available (list existing PR, create if missing). If `gh` is not installed or fails, show manual PR URL only and do not fail the workflow.
