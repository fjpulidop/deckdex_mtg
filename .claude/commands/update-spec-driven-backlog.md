---
name: "Update Spec-Driven Backlog"
description: "Analyze specs vs code, create/update/close GitHub Issues for spec gaps"
category: Workflow
tags: [workflow, explore, priorities, backlog, spec-driven, sync]
model: opus
---

Analyze the codebase against OpenSpec specifications to produce a verified backlog of spec gaps, then sync results to GitHub Issues labeled `spec-driven-backlog`. Use `/spec-backlog` to view the current state.

**Input:** $ARGUMENTS (optional: comma-separated areas to focus on, e.g. "UI/UX, Analytics". If empty, analyze all areas.)

**IMPORTANT: This command only modifies GitHub Issues.** You may read files, search code, and investigate the codebase, but you must NEVER write application code or implement features.

---

## Areas

Use these hardcoded area groupings. If the user passed specific areas as input, only analyze those.

| Area | Label | Spec directories |
|------|-------|-----------------|
| **UI/UX** | `area:ui-ux` | web-dashboard-ui, navigation-ui, landing-page, animated-backgrounds, accessible-modals, theme-preference, i18n, global-jobs-ui |
| **Cards & Collection** | `area:cards-collection` | card-detail-modal, card-image-storage, card-name-autocomplete, global-image-cache, import-resolve-review, catalog-system, image-store |
| **Decks** | `area:decks` | decks, deck-builder-ui |
| **Analytics & Prices** | `area:analytics-prices` | analytics-dashboard, collection-insights, price-updates, buffered-price-updates |
| **Backend & API** | `area:backend-api` | web-api-backend, architecture, data-model, sql-filtering-and-pagination, websocket-progress, import-routes-tests, api-tests |
| **Infra & DevOps** | `area:infra-devops` | ci-pipeline, test-infra, demo-mode |
| **Auth & Users** | `area:auth-users` | user-auth, user-profile, admin-backoffice, external-apis-settings |
| **Core/CLI** | `area:core-cli` | cli-interface, configuration-management, processor-configuration, processor-service-wrapper, verbose-logging, dry-run-mode, openai-integration |

---

## Execution

Launch a **single** analyst subagent (`subagent_type: Explore`, `run_in_background: true`) that analyzes all areas sequentially.

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
> 3. **Extract concrete deliverables from the spec** — For each spec, list the concrete things it requires:
>    - Backend: API endpoints (method + path), repository methods, service classes, migrations
>    - Frontend: pages, components, API client methods, hooks, i18n keys
>    - Tests: test files, test classes/functions
> 4. **Verify each deliverable against actual code** — This is the CRITICAL step. Do NOT estimate status from spec reading alone. For each deliverable:
>    - **Routes**: Read the route file. Count actual endpoint handlers vs spec requirements.
>    - **Components**: Glob for the component file. If it exists, read it briefly to confirm it's functional (not a stub).
>    - **Migrations**: Grep for table/column names in `migrations/`.
>    - **Tests**: Grep for test class/function names in `tests/`.
>    - **API client**: Grep for method names in `frontend/src/api/client.ts`.
>    - Calculate: `completion = verified_deliverables / total_deliverables`
> 5. **Assign status based on verification**, NOT speculation:
>    - **Done**: completion >= 90% (all major deliverables verified in code)
>    - **Mostly done**: completion 70-89% (core working, minor gaps)
>    - **Partial**: completion 30-69% (some deliverables exist, significant gaps)
>    - **Not started**: completion < 30% (little or no code found)
> 6. **Produce the area's output** as a markdown table with these columns:
>    - **#** (rank by priority — highest value/effort ratio first)
>    - **Item** (short name)
>    - **Description** (1 sentence: what REMAINS to be done, not the full feature)
>    - **Value** (High/Medium/Low — user impact)
>    - **Effort** (High/Medium/Low — effort for REMAINING work only)
>    - **Status** (one of: Not started | Partial | Mostly done | Done)
>    - **Completion** (X/Y deliverables verified — e.g. "8/10")
>    - **Missing** (list of unverified deliverables)
>    - **Evidence** (list of verified file paths)
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
> ```
> ## Project Backlog
>
> Generated: {DATE}
>
> ### {Area Name}
>
> | # | Item | Description | Value | Effort | Status | Completion |
> |---|------|-------------|-------|--------|--------|------------|
> | 1 | ... | ... | ... | ... | ... | 8/10 |
>
> (repeat for each area — if ALL items in an area are Done, just write "All items complete.")
>
> ---
>
> ### Quick Wins (cross-area)
>
> {Top 5 items across ALL areas that are NOT Done, High value + Low effort, with their area tag}
>
> ### Recommended Next Sprint
>
> {Top 3 items to implement next, considering:
> - Dependencies between items
> - Mix of areas for variety
> - Finishing partial work before starting new
> - ONLY items that are genuinely NOT Done (completion < 90%)}
> ```

---

## Assembly — GitHub Issues Sync

After the explorer agent completes:

1. **Display** the markdown backlog to the user.

2. **Fetch existing spec-driven backlog issues:**
   ```bash
   gh issue list --label "spec-driven-backlog" --state all --limit 200 --json number,title,labels,state,body
   ```
   Build a map of `title → issue` for matching.

3. **Create labels** (idempotent — skip if they exist):
   ```bash
   gh label create "spec-driven-backlog" --color "0E8A16" --description "Spec-driven backlog: gap between spec and code" 2>/dev/null || true
   ```
   For each area, create a label with the kebab-case name from the Areas table (e.g. `area:ui-ux`, `area:backend-api`).

4. **For each analyzed item, sync to GitHub Issues:**

   **If status is "Done":**
   - If an open issue exists with matching title → close it with a comment: `Verified complete ({completion}). Closing.`
   - If no issue exists → skip (don't create issues for done items)

   **If status is NOT "Done":**
   - If an open issue exists with matching title → update its body with fresh data (completion, missing deliverables, evidence)
   - If a closed issue exists → reopen it with updated body
   - If no issue exists → create a new one:
     ```bash
     gh issue create \
       --title "[Backlog] {Item name}" \
       --label "spec-driven-backlog,area:{area-kebab},enhancement" \
       --body "$(cat <<'EOF'
     > **This is a future feature spec, not a bug report.** It tracks planned work derived from the project's OpenSpec specifications.

     ## Overview

     | Field | Value |
     |-------|-------|
     | **Area** | {Area} |
     | **Value** | {High/Medium/Low} — {1-sentence justification} |
     | **Effort** | {High/Medium/Low} — {1-sentence justification} |
     | **Current Status** | {Status} ({X/Y} deliverables verified) |
     | **Spec source** | `openspec/specs/{spec-dir}/spec.md` |

     ## What remains

     {2-3 sentence description of what needs to be built to complete this feature. Focus on the gap between current state and spec requirements.}

     ## Missing deliverables

     ### Backend
     - [ ] {missing backend item 1 — e.g. "POST /api/foo endpoint (spec section 3.2)"}
     - [ ] {missing backend item 2}

     ### Frontend
     - [ ] {missing frontend item 1 — e.g. "FooComponent with filtering and pagination"}
     - [ ] {missing frontend item 2}

     ### Tests
     - [ ] {missing test item — e.g. "Integration tests for /api/foo routes"}

     _(Remove empty sections if all deliverables for a layer are complete)_

     ## Evidence of existing work

     Files that already exist and partially implement this feature:

     | File | What it covers |
     |------|---------------|
     | `{file1.py}` | {brief description} |
     | `{file2.tsx}` | {brief description} |

     ## Related specs & changes

     - Spec: `openspec/specs/{spec-dir}/spec.md`
     - Archived changes: {list any relevant archived changes, or "None"}

     ---
     _Auto-generated by `/update-spec-driven-backlog` on {DATE}_
     EOF
     )"
     ```

5. **Report** the sync results:
   ```
   Backlog sync complete:
   - Created: {N} new issues
   - Updated: {N} existing issues
   - Closed: {N} completed issues
   View at: https://github.com/{owner}/{repo}/issues?q=label:spec-driven-backlog
   ```
