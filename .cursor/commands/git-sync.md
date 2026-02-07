---
name: /git-sync
id: git-sync
category: Git
description: Quick git sync - add, commit, and push (no PR creation)
---

Quick git workflow for syncing changes: stage all changes, create commit, and push to remote. Does NOT create pull requests.

**Use this when:**
- You want to push commits to an existing feature branch
- You're making incremental progress and don't need a PR yet
- The PR already exists and you just want to add more commits
- You want a simpler, faster workflow without PR creation

**Use `/git-flow` when:**
- You're starting a new feature and need to create a PR
- You're not sure if a PR exists

**Input**: Optional custom commit message

**Steps**

1. **Stage all changes**
   ```bash
   git add -A
   git status --short
   ```
   Show what files are being staged.

2. **Create commit**
   
   a. Analyze changes and generate intelligent commit message
   b. Show generated message to user
   c. Create commit with approved message

3. **Push to remote**
   
   a. Check current branch
   b. If on main/master, warn and prompt for action:
      - Create feature branch and push
      - Push to main anyway (requires confirmation)
      - Cancel
   c. If on feature branch, push to remote
   d. Set upstream tracking if needed

4. **Show summary**

**Output On Success**

```
## Git Sync Complete ✅

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

---

**All changes synced!**

If you need to create a PR, run `/git-pr`
If a PR already exists, your commits have been added automatically.
```

**Output When Creating Feature Branch**

```
## Git Sync Complete ✅

### 1. Files Staged
- 5 files staged

### 2. Commit Created
- Commit: abc1234
- Message: feat: add new feature
- Files: 5 changed (+150, -20)

### 3. New Branch Created and Pushed
- Created branch: feat/add-feature
- Based on: main
- Remote: origin/feat/add-feature
- Commits pushed: 1

---

**Branch created and synced!**

To create a PR, run `/git-pr` or visit:
https://github.com/user/repo/compare/main...feat/add-feature
```

**Interactive Mode**

At each step, show:
```
[1/3] Staging changes... ✅ Done (11 files)
[2/3] Creating commit...
  
  Generated commit message:
  chore: archive config-centralized change and sync specs
  
  - Archive to 2026-02-07-config-centralized
  - Sync delta specs to main
  - Add configuration-management capability
  
  Use this message? [Yes/Edit/Cancel]

[3/3] Pushing to remote... ✅ Done (1 commit)
```

**Guardrails**
- Warn when attempting to push to main/master
- Show what will be staged before staging
- Show commit message before committing
- Never create PR automatically (that's `/git-flow` or `/git-pr`)
- If on main, strongly suggest creating feature branch
- Set upstream tracking automatically for new branches
- Show clear error messages if push fails

**Comparison with Other Commands**

| Command | Stage | Commit | Push | Create PR | Use When |
|---------|-------|--------|------|-----------|----------|
| `/git-sync` | ✅ | ✅ | ✅ | ❌ | Quick sync to existing branch |
| `/git-flow` | ✅ | ✅ | ✅ | ✅* | Complete workflow, creates PR if needed |
| `/git-add` | ✅ | ❌ | ❌ | ❌ | Just stage changes |
| `/git-commit` | ❌ | ✅ | ❌ | ❌ | Just commit staged changes |
| `/git-push` | ❌ | ❌ | ✅ | ❌ | Just push commits |
| `/git-pr` | ❌ | ❌ | ❌ | ✅ | Just create/update PR |

*`/git-flow` intelligently checks if PR exists and only creates if needed
