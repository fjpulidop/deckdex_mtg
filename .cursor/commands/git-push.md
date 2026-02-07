---
name: /git-push
id: git-push
category: Git
description: Push commits to remote (creates feature branch if needed)
---

Push commits to remote repository, creating a feature branch if needed.

**Input**: Optional branch name (defaults to intelligent naming based on commit)

**Steps**

1. **Check current branch**
   ```bash
   git branch --show-current
   ```

2. **Determine push strategy**

   **If on main/master:**
   - Warn user they're on main
   - Prompt for action:
     - "Create feature branch and push"
     - "Push to main anyway" (not recommended)
     - "Cancel"
   
   If "Create feature branch":
   - Generate branch name from latest commit or ask user
   - Format: `feat/description` or `fix/description`
   - Create and switch to branch
   
   **If on feature branch:**
   - Check if branch has remote tracking
   - If no tracking, push with `-u origin <branch>`
   - If has tracking, just push

3. **Check for unpushed commits**
   ```bash
   git log @{u}.. --oneline 2>/dev/null || git log --oneline -5
   ```
   Show commits that will be pushed.

4. **Push to remote**
   
   **If new branch:**
   ```bash
   git push -u origin <branch-name>
   ```
   
   **If existing branch:**
   ```bash
   git push
   ```

5. **Show push result**
   Display:
   - Branch pushed to
   - Number of commits pushed
   - Remote URL for creating PR

**Output On Success**

```
## Push Complete

**Branch:** feat/new-feature
**Remote:** origin/feat/new-feature
**Commits pushed:** 3

Pushed to: https://github.com/user/repo/tree/feat/new-feature

Ready to create PR. Use `/git-pr` to open a pull request.
```

**Output When Creating Branch**

```
## Branch Created and Pushed

**New branch:** feat/enhance-cli
**Based on:** main
**Commits:** 1

Branch pushed to: origin/feat/enhance-cli

Ready to create PR. Use `/git-pr` to open a pull request.
```

**Guardrails**
- Never force push without explicit user confirmation
- Warn when pushing to main/master
- Show what commits will be pushed before pushing
- Create feature branches with meaningful names
- Set upstream tracking for new branches
