# Agent Workflow Architecture

## Overview

The workflow system has three layers: **Feed** (populate backlogs), **View** (prioritize), and **Execute** (implement). Each layer uses specialized agents with models chosen for the task complexity.

## Layer 1: Backlog Feeding

| Command | Purpose | Agent | Model | GitHub Label |
|---------|---------|-------|-------|--------------|
| `/update-spec-driven-backlog` | Analyze specs vs code, find gaps | `Explore` (built-in) | *(environment default)* | `spec-driven-backlog` |
| `/update-product-driven-backlog` | Research competitors, generate new ideas | `Explore` (built-in) | *(environment default)* | `product-driven-backlog` |

Uses `Explore` (built-in, read-only) because it requires deep codebase exploration: reading specs, navigating code, comparing with competitors, and deducing what's missing. The orchestrator then creates/updates/closes GitHub Issues with the results.

**Incremental mode**: `/update-spec-driven-backlog` checks `git log` for recently changed specs and only re-analyzes affected areas, avoiding full re-analysis on every run.

## Layer 2: Viewers (read + prioritize)

| Command | Purpose | Agent | Model |
|---------|---------|-------|-------|
| `/spec-backlog` | Read Issues, group by area, propose top 3 | `analyst` | **Haiku** |
| `/product-backlog` | Read Issues, group by area, propose top 3 | `analyst` | **Haiku** |

Uses `analyst` (Haiku) because it's purely analytical work: reading structured data (GitHub Issues), parsing, grouping, and prioritizing. No code exploration needed.

## Layer 3: Implementation (`/implement`)

Unified pipeline that adapts based on input:

**Input modes:**
1. **Issues**: `/implement #85, #71, #63` -- implement specific GitHub Issues
2. **Text**: `/implement "add price history chart"` -- implement 1 feature from description
3. **Areas**: `/implement Analytics, UI` -- explore areas and choose what to build (fallback)

**Single mode** (1 feature): sequential, no worktree, runs in main repo.
**Multi mode** (N features): parallel, isolated worktrees per developer.

```
                    +-- text description ----------------+
                    |                                     |
Phase 0: Input -----+-- GitHub issues ------------------+
                    |                                     |
                    +-- areas (no issues) --+             |
                                            v             |
Phase 1: Explore --- N Product Managers     |             |
                     (only if no issues)    |             |
                            |               |             |
Phase 2: Select ---- Pick best ideas -------+             |
                            |                             |
                            v                             v
Phase 3a: Design --- N Architects (parallel, main repo)
                     Create OpenSpec artifacts:
                     proposal -> design -> delta-spec -> tasks
                     + context-bundle.md (compact reference for developer)
                            |
                     3a.1: Detect shared files, assign ownership
                     3a.2: Pre-validate (check file refs, layer tags)
                            |
                            v
Phase 3b: Build ---- Specialized Developers
                     Single: foreground, main repo
                     Multi:  background, isolated worktrees
                     Routing: backend-developer / frontend-developer / developer (full-stack)
                     Input: context-bundle + tasks + reviewer learnings
                            |
                     Post-flight: validate diffs vs expected
                            |
                            v
Phase 4a: Merge ---- Copy worktrees -> main repo
                     (skip in single mode)
                     Manual merge for shared files
                            |
                            v
Phase 4b: Review --- 1 Reviewer
                     |- CI: ruff + pytest + eslint + tsc + vitest
                     |- Fix cross-feature merge issues
                     |- Record learnings -> common-fixes.md
                     +- Archive: openspec sync-specs + archive
                            |
                            v
Phase 4c: Ship ----- Branch + commits + push + PR
                     (with Closes #XX for resolved issues)
                            |
                            v
Phase 4d: CI ------- Monitor GitHub Actions, fix if failing
                            |
                            v
Phase 4e: Report --- Summary table with status per feature
```

## Agent Types

| Agent | `subagent_type` | Model | Role | Model Justification |
|-------|----------------|-------|------|---------------------|
| **Product Manager** | `product-manager` | **Opus** | Ideation, brainstorming, product strategy | Requires creativity and deep reasoning |
| **Analyst** | `analyst` | **Haiku** | Parse Issues, group, prioritize | Mechanical task with structured data |
| **Architect** | `architect` | **Sonnet** | Design OpenSpec artifacts + context bundle | Good balance of technical design / cost |
| **Backend Developer** | `backend-developer` | **Sonnet** | Implement Python/FastAPI/PostgreSQL code | Specialized, lighter prompt (no frontend rules) |
| **Frontend Developer** | `frontend-developer` | **Sonnet** | Implement React/TypeScript/Tailwind code | Specialized, lighter prompt (no backend rules) |
| **Developer** | `developer` | **Sonnet** | Implement full-stack code | Used for mixed-layer features or single mode |
| **Reviewer** | `reviewer` | **Sonnet** | Quality gate + learnings + archival | Needs to understand code but not create from scratch |
| **Explore** | `Explore` | *(built-in)* | Read-only technical exploration | Controlled by Claude Code |

The **orchestrator** (the main conversation agent, Opus) handles Phase 0 (input parsing), Phase 2 (selection), Phase 4a (merge), and Phase 4c-e (ship). It retains full context across all features, which is critical for merge decisions and shared file conflict resolution.

## Token Optimization Features

### 1. Context Bundle (architect -> developer)

The architect produces a `context-bundle.md` alongside tasks.md. This is a compact reference (~200 lines) containing key patterns, function signatures, imports, and code snippets from every file the developer will need. The developer uses this instead of re-reading every referenced file from scratch, saving significant tokens on file reads.

### 2. Reviewer Feedback Loop (reviewer -> future developers)

After each sprint, the reviewer writes its fixes to `.claude/agent-memory/reviewer/common-fixes.md`. Before launching developers, the orchestrator reads this file and inlines it into the developer prompt as "Lessons from past reviews." This prevents developers from repeating the same mistakes across sprints (e.g., `scope="module"` instead of `scope="function"`, missing `ruff format`, ESLint rules).

### 3. Specialized Developers (backend vs frontend)

Instead of always using the full-stack `developer` agent (which carries Python + React + Tailwind + FastAPI rules), the orchestrator routes tasks to specialized agents:
- `backend-developer`: Only Python/FastAPI/PostgreSQL rules (~60% smaller prompt)
- `frontend-developer`: Only React/TypeScript/Tailwind rules (~60% smaller prompt)
- `developer`: Full-stack, used only when a feature spans both layers

Routing is based on layer tags (`[backend]`, `[frontend]`, `[core]`, `[test]`) assigned by the architect in tasks.md.

### 4. Incremental Backlog Analysis

`/update-spec-driven-backlog` checks git history for recently changed specs before launching the full explorer. If only 2 of 8 areas had spec changes, it only analyzes those 2 areas instead of all 8.

### 5. Pre-validation Post-Architect

Before launching developers (which are the most expensive phase), the orchestrator quick-checks the architect's output:
- Do referenced files actually exist?
- Are layer tags present?
- Does tasks.md have at least one task?

This catches architect hallucinations early, before wasting developer tokens on bad blueprints.

## Typical Flow

```
/update-spec-driven-backlog              <- Feed (Explore)
/update-product-driven-backlog           <- Feed (Explore)
        |
        v
/spec-backlog                            <- Prioritize (analyst, Haiku)
/product-backlog                         <- Prioritize (analyst, Haiku)
        |
        v
/implement #85, #71                      <- Execute:
                                            architect (Sonnet)
                                            -> backend-developer / frontend-developer (Sonnet)
                                            -> reviewer (Sonnet)
```

## File Structure

```
.claude/
|-- agents/
|   |-- product-manager.md               <- Opus
|   |-- analyst.md                       <- Haiku
|   |-- architect.md                     <- Sonnet
|   |-- backend-developer.md             <- Sonnet (backend specialist)
|   |-- frontend-developer.md            <- Sonnet (frontend specialist)
|   |-- developer.md                     <- Sonnet (full-stack fallback)
|   +-- reviewer.md                      <- Sonnet
|-- agent-memory/
|   |-- reviewer/common-fixes.md         <- Reviewer learnings (feedback loop)
|   |-- backend-developer/              <- Backend dev memory
|   |-- frontend-developer/             <- Frontend dev memory
|   |-- openspec-apply-developer/       <- Full-stack dev memory
|   |-- openspec-architect/             <- Architect memory
|   +-- product-ideation-explorer/      <- Product manager memory
|-- commands/
|   |-- implement.md                     <- Unified pipeline
|   |-- spec-backlog.md                  <- Spec viewer
|   |-- product-backlog.md               <- Product viewer
|   |-- update-spec-driven-backlog.md    <- Feed specs (incremental)
|   |-- update-product-driven-backlog.md <- Feed product
|   +-- opsx/                            <- Manual OpenSpec workflow
+-- skills/
    +-- openspec-*/SKILL.md              <- OpenSpec skills
```

## Design Decisions

**Why no merge agent?** The orchestrator (Opus) handles merge because it already has full context: which features were implemented, the shared file ownership plan from 3a.1, and what each developer changed. A separate agent would need all that context passed as prompt, duplicating what the orchestrator already knows.

**Why `Explore` for feeding and `analyst` for viewing?** Feeding requires deep codebase exploration (reading specs, verifying deliverables against actual code). Viewing only reads structured GitHub Issues -- purely mechanical parsing and prioritization.

**Why `product-manager` on Opus?** Product ideation requires creative reasoning, competitive analysis, and strategic thinking across multiple domains. Opus handles the ambiguity and open-endedness better than Sonnet.

**Why Sonnet for architect/developer/reviewer?** These agents have well-defined tasks with clear inputs (specs, artifacts, code). Sonnet provides excellent code generation and technical reasoning at lower cost than Opus.

**Why specialized developers?** A backend-only feature doesn't need React/TypeScript/Tailwind rules in its prompt. Splitting saves ~60% of prompt tokens per developer and reduces noise that could lead to irrelevant suggestions.

**Why single mode skips worktrees?** Worktree isolation adds overhead (create, merge, cleanup) that's unnecessary for a single feature with no parallel conflicts.

**Why reviewer records learnings?** The same CI fixes recur across sprints (scope="module", missing ruff format, ESLint hooks rules). Recording them once and feeding them to future developers breaks the cycle.
