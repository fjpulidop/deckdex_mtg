---
name: /git-add
id: git-add
category: Git
description: Add all changes to git staging area
---

Add all changes to git staging area, including new files, modifications, and deletions.

**Input**: None required

**Steps**

1. **Check git status**
   ```bash
   git status
   ```
   Show current state to user.

2. **Add all changes**
   ```bash
   git add -A
   ```
   This stages:
   - New files (untracked)
   - Modified files
   - Deleted files

3. **Show staged changes**
   ```bash
   git status --short
   ```
   Display what was staged with status codes:
   - `M` = Modified
   - `A` = Added (new file)
   - `D` = Deleted
   - `R` = Renamed

**Output**

```
## Files Staged

Staged N files:
- M  README.md
- A  src/new-feature.ts
- D  old-file.ts
- M  package.json

Ready for commit. Use `/git-commit` to create a commit.
```

**Guardrails**
- Always show what was staged
- If no changes to stage, inform user
- Don't commit automatically - that's a separate command
