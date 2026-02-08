---
name: /git-pr
id: git-pr
category: Git
description: Create a GitHub Pull Request with detailed description
---

Create a GitHub Pull Request with an intelligent, comprehensive description.

**Input**: None required (generates description from commits and changes)

**Steps**

1. **Verify prerequisites**

   a. Check current branch is not main/master:
   ```bash
   git branch --show-current
   ```
   If on main, inform user to switch to feature branch.

   b. Check branch is pushed to remote:
   ```bash
   git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null
   ```
   If not pushed, prompt user to run `/git-push` first.

2. **Gather PR context**

   a. **Get commits for this branch:**
   ```bash
   git log origin/main..HEAD --oneline
   ```
   
   b. **Get detailed diff statistics:**
   ```bash
   git diff origin/main..HEAD --stat
   ```
   
   c. **Get full diff for analysis:**
   ```bash
   git diff origin/main..HEAD
   ```

3. **Check for GitHub CLI**
   ```bash
   which gh
   ```
   
   **If `gh` is available:** Use it to create PR directly
   **If `gh` is not available:** Generate PR URL and description for manual creation

4. **Generate PR content**

   **Title:** Use first commit message or generate from changes
   
   **Description template:**
   ```markdown
   ## Summary
   [Brief overview of what this PR does - 1-2 sentences]
   
   ## Changes
   [Detailed list of changes - use commits and diff analysis]
   - ✅ Added X feature
   - ♻️ Refactored Y component  
   - 🐛 Fixed Z bug
   - 📚 Updated documentation
   
   ## Why
   [Explain the motivation - what problem does this solve?]
   
   ## Testing
   - [x] All tests passing
   - [x] Backwards compatibility maintained
   - [ ] Manual testing required
   
   ## Breaking Changes
   [List any breaking changes, or state "None"]
   
   ## Screenshots/Examples
   [Optional - include if relevant]
   
   ## Checklist
   - [x] Tests added/updated
   - [x] Documentation updated
   - [x] No new warnings
   - [x] Backwards compatible (or breaking changes documented)
   ```

5. **Show generated PR content to user**

   Display the title and description and ask:
   - "Create PR with this description"
   - "Edit description" (let user modify)
   - "Cancel"

6. **Create the PR**

   **If using GitHub CLI:** Always pass a description. Never run `gh pr create` without `--body`.
   ```bash
   gh pr create --title "Title" --body "Description"
   ```
   Use the generated description (from step 4) as the body. Write the description **in English**.
   
   **If no GitHub CLI:**
   - Generate GitHub URL: `https://github.com/owner/repo/compare/main...branch?expand=1`
   - Copy description to clipboard if possible
   - Show instructions for manual PR creation

7. **Show PR result**

   Display:
   - PR number and URL
   - Title
   - Status (draft vs ready for review)

**Output On Success (with gh CLI)**

```
## Pull Request Created

**PR #42:** feat: Enhanced CLI with configuration options
**URL:** https://github.com/user/repo/pull/42
**Status:** Ready for review

**Summary:**
Enhanced CLI with 13+ configuration options, centralized configuration system, 
and architecture improvements while maintaining 100% backwards compatibility.

**Changes:**
- 23 files changed (+2,525, -228)
- 36 tests passing
- Documentation updated

View PR: https://github.com/user/repo/pull/42
```

**Output On Success (without gh CLI)**

```
## Pull Request Ready

**Branch:** feat/enhance-cli
**Target:** main

**Create PR manually:**
👉 https://github.com/user/repo/compare/main...feat/enhance-cli?expand=1

**PR Description** (copied below, paste it into GitHub):

---

[Generated PR description here]

---

Alternative: Install GitHub CLI for automatic PR creation:
brew install gh
```

**Guardrails**
- Don't create PR from main branch
- Verify branch is pushed before creating PR
- **Always** generate and pass a PR description (body); never create a PR without a body
- Write the PR description **in English**
- Generate comprehensive, well-formatted description (Summary, Changes, Why, etc.)
- Include test results and breaking changes when relevant
- Use emoji sparingly and meaningfully (✅ 🐛 📚 ♻️)
- Always show description before creating
- Provide fallback for manual PR creation if gh CLI unavailable
