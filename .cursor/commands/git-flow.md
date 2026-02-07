---
name: /git-flow
id: git-flow
category: Git
description: Complete git workflow - add, commit, push, and create PR
---

Execute the complete git workflow: stage changes, create commit, push to remote, and open a pull request.

**Input**: Optional custom commit message or branch name

**Steps**

This command orchestrates the full git workflow by executing the individual git commands in sequence.

1. **Stage all changes** (`/git-add`)
   ```bash
   git add -A
   git status --short
   ```
   Show what files are being staged.

2. **Create commit** (`/git-commit`)
   
   a. Analyze changes and generate intelligent commit message
   b. Show generated message to user
   c. Prompt for confirmation or edits
   d. Create commit with approved message

3. **Push to remote** (`/git-push`)
   
   a. Check current branch
   b. If on main, create feature branch (prompt for name)
   c. Push commits to remote
   d. Show push result

4. **Check if PR needed** (SMART PR LOGIC)
   
   a. Check if PR already exists for current branch
      ```bash
      gh pr list --head <branch-name> --json number,url
      ```
   
   b. Decision logic:
      - **If PR exists**: Skip PR creation, show existing PR URL
      - **If no PR exists**: Proceed to create PR
      - **If gh CLI not available**: Show manual PR creation URL
   
   c. If creating PR:
      - Generate comprehensive PR description from commits and changes
      - Show PR content to user
      - Create PR (using gh CLI if available)
      - Show PR URL

5. **Show complete summary**

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

**Next steps:**
- View PR: https://github.com/user/repo/pull/42
- Assign reviewers
- Wait for CI checks
```

**Output On Complete Success (PR Already Exists)**

```
## Git Workflow Complete ✅

### 1. Files Staged
- 11 files staged (1 new, 2 modified, 8 renamed)

### 2. Commit Created
- Commit: 72ff956
- Message: chore: archive config-centralized change
- Files: 11 changed (+443, -52)

### 3. Pushed to Remote
- Branch: feat/incremental-price-updates
- Remote: origin/feat/incremental-price-updates
- Commits pushed: 1

### 4. Pull Request
- ℹ️  PR already exists for this branch
- PR #5: feat: Incremental Price Updates
- URL: https://github.com/user/repo/pull/5
- Status: Your new commits have been added to the existing PR

---

**Next steps:**
- View updated PR: https://github.com/user/repo/pull/5
- New commits will appear in the PR automatically
```

**Output On Partial Success**

```
## Git Workflow Partial Complete

✅ Completed:
1. Files staged (23 files)
2. Commit created (abc1234)
3. Pushed to remote (feat/enhance-cli)

⏸️ Stopped at:
4. Pull Request (user chose to create manually)

**To complete:**
Create PR manually: https://github.com/user/repo/compare/main...feat/enhance-cli

Or run `/git-pr` later to create PR.
```

**Interactive Mode**

At each step, show:
```
[1/4] Staging changes... ✅ Done
[2/4] Creating commit...
  
  Generated commit message:
  feat: enhance CLI with configuration options
  
  - Added 13+ CLI options
  - Centralized configuration  
  - 100% backwards compatible
  
  Use this message? [Yes/Edit/Cancel]
```

**Guardrails**
- Stop on any errors and show clear message
- Allow user to cancel at any step
- Show progress clearly with checkboxes/emojis
- Provide fallback instructions if tools unavailable
- Never force actions without confirmation
- Each step uses the individual command logic
- If user cancels, show what was completed and what remains
- **SMART PR DETECTION**: Check if PR exists before attempting to create
- If PR exists, skip creation and show existing PR URL with note that commits were added
- If gh CLI unavailable, provide manual PR URL but don't fail the workflow
