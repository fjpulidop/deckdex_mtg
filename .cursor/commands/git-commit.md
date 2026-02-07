---
name: /git-commit
id: git-commit
category: Git
description: Create a git commit with an intelligent, detailed message
---

Create a git commit with an intelligent, context-aware commit message.

**Input**: Optional custom message or let AI generate one based on changes

**Steps**

1. **Check for staged changes**
   ```bash
   git diff --cached --stat
   ```
   If no staged changes, prompt user to run `/git-add` first.

2. **Analyze changes to generate commit message**

   If user provided a message, use it. Otherwise:

   a. **Read the diff** to understand what changed:
   ```bash
   git diff --cached
   ```

   b. **Check recent commits** for style:
   ```bash
   git log -5 --oneline
   ```

   c. **Generate intelligent commit message** following conventional commits format:
   
   **Format:**
   ```
   <type>: <subject>
   
   <body>
   
   <footer>
   ```
   
   **Types:**
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation changes
   - `refactor`: Code refactoring
   - `test`: Adding/updating tests
   - `chore`: Maintenance tasks
   - `perf`: Performance improvements
   - `style`: Code style changes (formatting, etc)
   
   **Guidelines for message:**
   - Subject: Clear, concise (50 chars or less)
   - Body: Explain WHAT changed and WHY (not how)
   - Include bullet points for multiple changes
   - Mention breaking changes if any
   - Reference issue numbers if applicable

3. **Show generated message to user**

   Display the commit message and ask for confirmation:
   - "Use this message"
   - "Edit message" (let user provide custom message)
   - "Cancel"

4. **Create commit**
   ```bash
   git commit -m "$(cat <<'EOF'
   [generated message here]
   EOF
   )"
   ```

5. **Show commit result**
   ```bash
   git log -1 --stat
   ```

**Output On Success**

```
## Commit Created

**Commit:** abc1234
**Message:** feat: add new feature

feat: add new feature

- Implemented X functionality
- Added Y component
- Updated documentation

Closes #123

**Files changed:** 5 files, +200 insertions, -50 deletions

Ready to push. Use `/git-push` to push to remote.
```

**Guardrails**
- Always show the message before committing
- Follow conventional commits format
- Include detailed body for substantial changes
- Mention breaking changes clearly
- Don't push automatically - that's a separate command
