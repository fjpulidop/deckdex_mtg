# Agents (Cursor) for DeckDex MTG

Purpose
-------
This document lists the local agents and skills available for the DeckDex MTG repository, explains their responsibilities and when to use them, and provides quick examples for invoking or extending them in the Cursor environment.

Where skills live
-----------------
- All agent skills live under `.cursor/skills/` as a folder per skill. Each skill contains a `SKILL.md` describing its behavior, inputs, and guardrails.

Available skills (summary)
--------------------------
- `openspec-apply-change` (.cursor/skills/openspec-apply-change/SKILL.md)
  - Purpose: Implement tasks from an OpenSpec change. Use when you want an assistant to apply a change's tasks directly to the codebase.
  - When to use: Starting or continuing implementation of a spec-driven change.

- `openspec-continue-change` (.cursor/skills/openspec-continue-change/SKILL.md)
  - Purpose: Create the next artifact for an OpenSpec change or continue the workflow when artifacts are missing.
  - When to use: You need to progress a change that is blocked by missing artifacts.

- `openspec-ff-change` (.cursor/skills/openspec-ff-change/SKILL.md)
  - Purpose: Fast-forward through OpenSpec artifact creation.
  - When to use: When you want to quickly generate all artifacts required to implement a change.

- `openspec-new-change` (.cursor/skills/openspec-new-change/SKILL.md)
  - Purpose: Start a new OpenSpec change using the experimental artifact workflow.
  - When to use: Create a new feature/fix/change with an OpenSpec workflow.

- `openspec-verify-change` (.cursor/skills/openspec-verify-change/SKILL.md)
  - Purpose: Verify that implementation matches change artifacts before archiving.
  - When to use: Final verification and readiness check before archiving a change.

- `openspec-explore` (.cursor/skills/openspec-explore/SKILL.md)
  - Purpose: Explore the codebase to answer questions and surface relevant files.
  - When to use: Investigating architecture, locating code paths, or preparing a design decision.

- Cursor helper skills (create-rule, create-skill, update-cursor-settings)
  - Purpose: Authoring and updating Cursor rules, creating new skills, and adjusting cursor settings.
  - When to use: Project-level meta tasks related to Cursor and skills.

How to use these agents
-----------------------
- Read the skill file first: open `.cursor/skills/<skill>/SKILL.md` to understand its inputs and guardrails.
- Typical workflow:
  1. Choose the relevant skill for your goal (apply, continue, explore, verify, etc).
  2. Invoke the skill via Cursor's agent/task UI or CLI integration (the IDE provides buttons/commands to run skills).
  3. Provide requested inputs (change name, target files, or confirmations).
  4. Review and approve any automated edits before committing.

Best practices
--------------
- Always inspect the SKILL.md content before running a skill that writes changes.
- Run skills in small steps for large changes; prefer "continue" or "apply" iteratively.
- Keep secrets and credentials out of automated inputs. Use environment variables and CI secrets.
- Add tests and run linters after automated edits. The skills are designed to leave code in a runnable state but manual checks are recommended.

Extending or adding new skills
-----------------------------
1. Create a new directory under `.cursor/skills/your-skill-name/`.
2. Add a `SKILL.md` with metadata, description, and step-by-step behavior following existing examples.
3. Include guardrails: when to pause, what to ask the user, and what files the skill may modify.
4. Test the skill locally in a safe branch before relying on it for major edits.

Security & Safety
-----------------
- Skills can modify the repository—treat them as privileged automation.
- Do not store secrets in SKILL.md or inside the repo. Use external secret managers for CI.
- Review all automated changes before merging to protected branches.

Troubleshooting
---------------
- If a skill reports "blocked" or "missing artifacts", open the related spec files in `openspec/` and resolve the missing pieces.
- If a skill produces problematic edits, revert the changes locally, update the SKILL.md to clarify behavior, and re-run.

Contact / Maintainers
---------------------
For questions about a specific skill or to request a new helper, open an issue and tag the repository maintainers.

