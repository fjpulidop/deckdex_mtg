---
name: "OPSX: Backlog"
description: "Analyze all project areas and return prioritized work items per area"
category: Workflow
tags: [workflow, explore, priorities, backlog]
---

Generate a prioritized project backlog by analyzing specs, archived changes, and actual code.

**Input:** $ARGUMENTS (optional: comma-separated areas to focus on, e.g. "UI/UX, Analytics". If empty, analyze all areas.)

**IMPORTANT: This is a read-only exploration command.** You may read files, search code, and investigate the codebase, but you must NEVER write code or implement features. Your only output is the backlog analysis.

---

## Areas

Use these hardcoded area groupings. If the user passed specific areas as input, only analyze those.

| Area | Spec directories |
|------|-----------------|
| **UI/UX** | web-dashboard-ui, navigation-ui, landing-page, animated-backgrounds, accessible-modals, theme-preference, i18n, global-jobs-ui |
| **Cards & Collection** | card-detail-modal, card-image-storage, card-name-autocomplete, global-image-cache, import-resolve-review, catalog-system, image-store |
| **Decks** | decks, deck-builder-ui |
| **Analytics & Prices** | analytics-dashboard, collection-insights, price-updates, buffered-price-updates |
| **Backend & API** | web-api-backend, architecture, data-model, sql-filtering-and-pagination, websocket-progress, import-routes-tests, api-tests |
| **Infra & DevOps** | ci-pipeline, test-infra, demo-mode |
| **Auth & Users** | user-auth, user-profile, admin-backoffice, external-apis-settings |
| **Core/CLI** | cli-interface, configuration-management, processor-configuration, processor-service-wrapper, verbose-logging, dry-run-mode, openai-integration |

---

## Execution

Launch a **single** analyst subagent (`subagent_type: analyst`, `run_in_background: true`) that analyzes all areas sequentially.

The explorer agent receives this prompt:

> You are analyzing the DeckDex MTG project to produce a prioritized backlog across all areas.
>
> **Areas to analyze (in order):**
>
> | Area | Spec directories |
> |------|-----------------|
> | UI/UX | web-dashboard-ui, navigation-ui, landing-page, animated-backgrounds, accessible-modals, theme-preference, i18n, global-jobs-ui |
> | Cards & Collection | card-detail-modal, card-image-storage, card-name-autocomplete, global-image-cache, import-resolve-review, catalog-system, image-store |
> | Decks | decks, deck-builder-ui |
> | Analytics & Prices | analytics-dashboard, collection-insights, price-updates, buffered-price-updates |
> | Backend & API | web-api-backend, architecture, data-model, sql-filtering-and-pagination, websocket-progress, import-routes-tests, api-tests |
> | Infra & DevOps | ci-pipeline, test-infra, demo-mode |
> | Auth & Users | user-auth, user-profile, admin-backoffice, external-apis-settings |
> | Core/CLI | cli-interface, configuration-management, processor-configuration, processor-service-wrapper, verbose-logging, dry-run-mode, openai-integration |
>
> If the user passed specific areas as input, only analyze those. Otherwise analyze all.
>
> ### For each area, follow these steps
>
> 1. **Read each spec** in `openspec/specs/{dir}/spec.md` for the area's directories
> 2. **Check archived changes** — scan `openspec/changes/archive/` for directory names containing keywords from the specs (e.g. for "decks" spec, look for archives with "deck" in the name). Read the `proposal.md` of matching archives to understand what was already implemented.
> 3. **Check actual code** — For each spec, verify what actually exists in the codebase:
>    - Use Glob/Grep to find relevant source files
>    - Check if routes, components, tests, migrations mentioned in specs actually exist
>    - Note gaps between spec and reality
> 4. **Produce the area's output** as a markdown table with these columns:
>    - **#** (rank by priority — highest value/effort ratio first)
>    - **Item** (short name)
>    - **Description** (1 sentence: what needs to be done)
>    - **Value** (High/Medium/Low — user impact)
>    - **Effort** (High/Medium/Low — implementation complexity)
>    - **Status** (one of: Not started | Partial | Mostly done | Done)
>
> ### Priority rules
> - Items that are "Partial" with High value go first (finish what's started)
> - High value + Low effort next (quick wins)
> - High value + Medium effort next
> - Low value or High effort items go last
> - Items marked "Done" go at the bottom for reference
>
> ### Output format
>
> Return the complete backlog as a single markdown document:
>
> ```
> ## Project Backlog
>
> Generated: {DATE}
>
> ### {Area Name}
>
> | # | Item | Description | Value | Effort | Status |
> |---|------|-------------|-------|--------|--------|
> | 1 | ... | ... | ... | ... | ... |
>
> (repeat for each area — if ALL items in an area are Done, just write "All items complete.")
>
> ---
>
> ### Quick Wins (cross-area)
>
> {Top 5 items across ALL areas that are High value + Low effort, with their area tag}
>
> ### Recommended Next Sprint
>
> {Top 3 items to implement next, considering:
> - Dependencies between items
> - Mix of areas for variety
> - Finishing partial work before starting new}
> ```

---

## Assembly

After the explorer agent completes, output its result directly to the user. Do NOT write it to a file.
