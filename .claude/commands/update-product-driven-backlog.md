---
name: "Update Product-Driven Backlog"
description: "Generate new feature ideas through product discovery, create GitHub Issues"
category: Workflow
tags: [workflow, explore, priorities, backlog, product-discovery]
model: opus
---

Analyze the project from a **product perspective** to generate new feature ideas that don't exist in specs yet. Syncs results to GitHub Issues labeled `product-driven-backlog`. Use `/product-backlog` to view current ideas.

**Input:** $ARGUMENTS (optional: comma-separated areas to focus on, e.g. "UI/UX, Decks". If empty, analyze all areas.)

**IMPORTANT: This command only creates GitHub Issues.** You may read files and search code to understand current capabilities, but you must NEVER write application code or implement features.

---

## Areas

| Area | Label | Focus |
|------|-------|-------|
| **UI/UX** | `area:ui-ux` | Dashboard experience, navigation, visual polish, accessibility, responsiveness |
| **Cards & Collection** | `area:cards-collection` | Card browsing, searching, filtering, image display, collection management |
| **Decks** | `area:decks` | Deck building, editing, sharing, importing/exporting, deck analysis |
| **Analytics & Prices** | `area:analytics-prices` | Price tracking, collection value, market trends, investment insights |
| **Backend & API** | `area:backend-api` | API capabilities, performance, real-time features, data access |
| **Infra & DevOps** | `area:infra-devops` | Deployment, monitoring, developer experience, CI/CD |
| **Auth & Users** | `area:auth-users` | User experience, profiles, social features, permissions |
| **Core/CLI** | `area:core-cli` | CLI tools, automation, batch operations, integrations |

---

## Execution

Launch a **single** explorer subagent (`subagent_type: Explore`, `run_in_background: true`) for product discovery.

The explorer agent receives this prompt:

> You are a product strategist analyzing the DeckDex MTG project to generate new feature ideas.
>
> **Your goal:** For each area, propose 2-4 new features that would significantly improve the user experience. These should be features that **don't exist yet** — not gaps in existing specs.
>
> **Areas to analyze:** {all areas or filtered by user input}
>
> ### Research steps
>
> 1. **Understand current capabilities** — Read the main codebase structure to understand what already exists:
>    - Glob for pages: `frontend/src/pages/*.tsx`
>    - Glob for components: `frontend/src/components/*.tsx`
>    - Read route files: `backend/api/routes/*.py`
>    - Read the API client: `frontend/src/api/client.ts`
>    - Skim existing specs: `openspec/specs/*/spec.md` (just titles and overview sections)
>
> 2. **Check existing backlog** — Read open issues to avoid duplicating existing spec-driven work:
>    ```bash
>    gh issue list --label "spec-driven-backlog" --state open --limit 100 --json title
>    gh issue list --label "product-driven-backlog" --state open --limit 100 --json title
>    ```
>    Do NOT propose features that already have open issues.
>
> 3. **Think like a user** — For each area, consider:
>    - What would a competitive MTG collection manager offer? (Moxfield, Archidekt, EDHREC, Scryfall, MTGGoldfish)
>    - What common workflows are clunky or missing?
>    - What data is available but not surfaced to the user?
>    - What would make users come back daily?
>    - What would make users recommend this to friends?
>
> 4. **For each idea, produce:**
>    - **Feature name** (short, descriptive)
>    - **User story** ("As a [user type], I want to [action] so that [benefit]")
>    - **Feature description** (2-3 sentences describing the feature, what it would look like, and how it would work)
>    - **Value** (High/Medium/Low — with justification focused on user impact)
>    - **Effort** (High/Medium/Low — with justification based on what infrastructure already exists vs what needs to be built)
>    - **Inspiration** (which competitor or product pattern inspired this, if any)
>    - **Prerequisites** (what existing features or infrastructure this depends on)
>    - **Area** (which area this belongs to)
>
> ### Priority rules
> - Features that leverage existing infrastructure (low effort, high value) first
> - Features that increase daily engagement next
> - Features that differentiate from competitors next
> - Complex features with uncertain value last
>
> ### Output format
>
> ```
> ## Product Discovery
>
> Generated: {DATE}
>
> ### {Area Name}
>
> | # | Feature | Value | Effort | Inspiration |
> |---|---------|-------|--------|-------------|
> | 1 | ... | High | Low | Moxfield |
>
> #### Feature: {name}
> - **User story:** As a {user}, I want to {action} so that {benefit}
> - **Description:** {2-3 sentences}
> - **Value:** {level} — {justification}
> - **Effort:** {level} — {justification}
> - **Inspiration:** {source}
> - **Prerequisites:** {list or "None"}
>
> (repeat for each feature, then each area)
>
> ---
>
> ### Top 5 Ideas (cross-area)
>
> {The 5 best ideas ranked by value/effort ratio, with area tag}
> ```

---

## Assembly — GitHub Issues Sync

After the explorer agent completes:

1. **Display** the product discovery results to the user.

2. **Fetch existing product-driven backlog issues:**
   ```bash
   gh issue list --label "product-driven-backlog" --state all --limit 200 --json number,title,labels,state,body
   ```
   Build a map of `title → issue` to avoid duplicates.

3. **Create labels** (idempotent):
   ```bash
   gh label create "product-driven-backlog" --color "7057FF" --description "Product-driven backlog: new feature idea" 2>/dev/null || true
   ```
   Area labels should already exist from spec-driven backlog; create if missing.

4. **For each proposed feature, create a GitHub Issue** (skip if an issue with similar title already exists):
   ```bash
   gh issue create \
     --title "[Product] {Feature name}" \
     --label "product-driven-backlog,area:{area-kebab},enhancement" \
     --body "$(cat <<'EOF'
   > **This is a product feature idea, not a bug report.** It was generated through product discovery analysis and has no existing spec yet.

   ## Overview

   | Field | Value |
   |-------|-------|
   | **Area** | {Area} |
   | **Value** | {High/Medium/Low} — {justification} |
   | **Effort** | {High/Medium/Low} — {justification} |
   | **Inspiration** | {source or "Original idea"} |
   | **Prerequisites** | {list or "None"} |

   ## User Story

   As a **{user type}**, I want to **{action}** so that **{benefit}**.

   ## Feature Description

   {2-3 sentence description of the feature, what it would look like, and how it would work.}

   ## Implementation Notes

   {Brief notes on what infrastructure exists that could be leveraged, and what would need to be built from scratch. Reference actual files/patterns in the codebase.}

   ---
   _Auto-generated by `/update-product-driven-backlog` on {DATE}_
   EOF
   )"
   ```

5. **Report** the sync results:
   ```
   Product discovery complete:
   - Created: {N} new feature ideas
   - Skipped: {N} duplicates (already exist as issues)
   View at: https://github.com/{owner}/{repo}/issues?q=label:product-driven-backlog
   ```
