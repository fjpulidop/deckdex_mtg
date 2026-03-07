---
name: "Spec Backlog"
description: "View spec-driven backlog from GitHub Issues and propose top 3 for implementation"
category: Workflow
tags: [workflow, backlog, viewer, spec-driven]
model: haiku
---

Display the spec-driven backlog by reading GitHub Issues labeled `spec-driven-backlog`. These are items derived from OpenSpec specifications — gaps between what specs require and what code exists. Use `/update-spec-driven-backlog` to refresh.

**Input:** $ARGUMENTS (optional: comma-separated areas to filter, e.g. "UI/UX, Analytics". If empty, show all.)

---

## Execution

1. **Fetch all open spec-driven backlog issues:**
   ```bash
   gh issue list --label "spec-driven-backlog" --state open --limit 100 --json number,title,labels,body
   ```

2. **Parse each issue** to extract metadata from the body:
   - **Area**: from `area:*` label (e.g. `area:ui-ux` → "UI/UX")
   - **Value / Effort / Status / Completion**: from the body's Overview table
   - **What remains**: from the body's "What remains" section

3. **Group by area** using this label-to-name mapping:

   | Label | Area Name |
   |-------|-----------|
   | `area:ui-ux` | UI/UX |
   | `area:cards-collection` | Cards & Collection |
   | `area:decks` | Decks |
   | `area:analytics-prices` | Analytics & Prices |
   | `area:backend-api` | Backend & API |
   | `area:infra-devops` | Infra & DevOps |
   | `area:auth-users` | Auth & Users |
   | `area:core-cli` | Core/CLI |

   If the user passed specific areas as input, only show those.

4. **Display** as a formatted table per area, then **propose the top 3 items** for implementation:

   ```
   ## Spec-Driven Backlog

   {N} open issues | Source: OpenSpec specifications

   ### {Area Name}

   | # | Issue | Description | Value | Effort | Status | Completion |
   |---|-------|-------------|-------|--------|--------|------------|
   | 1 | #42 Item name | What remains... | High | Low | Partial | 5/10 |

   (repeat for each area with open issues)

   ---

   ## Recommended Next Sprint (Top 3)

   These are the top 3 spec-driven items to implement next, ranked by value/effort ratio:

   | Priority | Issue | Area | Value | Effort | Rationale |
   |----------|-------|------|-------|--------|-----------|
   | 1 | #XX Item | Area | High | Low | {why this should be next} |
   | 2 | #XX Item | Area | High | Medium | {why} |
   | 3 | #XX Item | Area | High | Medium | {why} |

   Run `/parallel-implement` to start implementing these items.
   ```

5. If no issues exist, tell the user:
   ```
   No spec-driven backlog issues found. Run `/update-spec-driven-backlog` to analyze the project and create issues.
   ```
