---
name: /git-flow
id: git-flow
category: Git
description: Complete git workflow - add, commit, push, and create PR (always branch from main)
---

Execute the complete git workflow: stage changes, create commit (on a branch from main), push, and show the link to create a PR in the browser (no `gh`).

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
   - **Use the generated message by default.** Only if the user provided a custom message as input, use that instead. Show the chosen message in the summary at the end; do not prompt "Use this message? [Yes/Edit/Cancel]".

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
   - Derive **branch name** from the commit message first line:
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
     git commit -m "<commit message>"
     ```
   - Continue to step 4 (Push).
   
   **c. If current branch is a feature branch (not main):**
   - **Default: create a new branch from main** so each change set has its own branch. Do not ask; do: stash → checkout main → pull → derive branch name from commit message → `git checkout -b <branch>` → stash pop → add → commit. Then continue to step 4.
   - **Exception:** Only commit on the current branch without re-branching when the user explicitly says to use the current branch, or when the staged changes are a direct continuation of the current branch name (e.g. branch `fix/dashboard-bugs` and only dashboard fix files changed).

4. **Push to remote** (`/git-push`)
   - If new branch: `git push -u origin <branch-name>`.
   - If existing branch: `git push`.
   - Show branch name, remote, and number of commits pushed.

5. **Show PR link**
   - Do **not** use GitHub CLI (`gh`). Always show the manual compare URL so the user can open the PR in the browser:
   - `https://github.com/<owner>/<repo>/compare/main...<branch-name>`
   - Obtain `<owner>/<repo>` from `git remote get-url origin` (e.g. `https://github.com/fjpulidop/deckdex_mtg` → owner `fjpulidop`, repo `deckdex_mtg`).

6. **Show complete summary** (what was staged, commit hash and message, branch, push result, and the compare URL for creating the PR).

**Checkpoints**

Show progress (e.g. [1/5] … [5/5]). Proceed through all steps without pausing for confirmation unless the user interrupts or there is an error. If the user says "stop" or "cancel", show what was completed and what remains.

**Output On Complete Success**

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

### 4. Create PR
- Open in browser: https://github.com/owner/repo/compare/main...feat/enhance-cli
```

**Guardrails**

- **Never commit to main** in this workflow: when on main, always create a branch from an up-to-date main first, then commit on that branch.
- **Always base new branches on main:** after `git checkout main`, run `git pull` before `git checkout -b <name>`.
- Stop on any errors and show a clear message.
- Allow user to cancel at any step; show what was completed and what remains.
- Show progress clearly (e.g. [1/5] … [5/5]).
- **Branch naming:** derive from commit message; keep type (feat/fix/docs/etc.) and a short slug; user can override if they provide a branch name as input.
- **Fewer prompts:** Use the generated commit message by default; create a new branch from main by default when on a feature branch (unless changes clearly extend that branch). Do not ask "Use this message?" or "Create new branch?" unless the user has explicitly asked to be prompted.
- **PR:** Do not use `gh`. Always show the GitHub compare URL so the user can create the PR in the browser. Derive owner/repo from `git remote get-url origin`.
