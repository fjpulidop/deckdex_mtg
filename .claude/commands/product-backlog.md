---
name: "Product Backlog"
description: "View product-driven backlog from GitHub Issues and propose top 3 for implementation"
category: Workflow
tags: [workflow, backlog, viewer, product-driven]
---

Display the product-driven backlog by reading GitHub Issues labeled `product-driven-backlog`. These are new feature ideas generated through product discovery — features that don't have specs yet but would improve the product. Use `/update-product-driven-backlog` to generate new ideas.

**Input:** $ARGUMENTS (optional: comma-separated areas to filter, e.g. "UI/UX, Analytics". If empty, show all.)

---

## Phase 0: Environment Pre-flight

Before fetching issues, detect if we're in a cloud/remote environment and ensure `gh` CLI is available.

### Detection

```bash
if [ "$CLAUDE_CODE_REMOTE" = "true" ] || [[ "$CLAUDE_CODE_ENTRYPOINT" == remote_* ]]; then
  echo "CLOUD_ENV=true"
fi
```

### GitHub CLI check

```bash
gh auth status 2>&1
```

- If `gh` is authenticated: set `GH_AVAILABLE=true`, proceed to Execution.
- If `gh` is NOT authenticated and we're in a cloud environment:
  - Check if the git remote uses a local proxy (`127.0.0.1`):
    ```bash
    git remote get-url origin 2>/dev/null
    ```
  - If local proxy detected, try to configure `gh` to work through it.
  - If `gh` still can't authenticate: set `GH_AVAILABLE=false`.

### When `GH_AVAILABLE=false`

**Stop and inform the user.** Do NOT attempt to generate or synthesize backlog data. Display:

```
## Product-Driven Backlog — Unavailable

GitHub CLI is not authenticated. This command requires `gh` to fetch issues from GitHub.

**You are in a cloud environment** where `gh` API access is not available through the local proxy.

### What you can do:
- **From a local terminal** with `gh` authenticated: run `/product-backlog` to see the full backlog.
- **To refresh the backlog**: run `/update-product-driven-backlog` from a local terminal — it will generate feature ideas and create GitHub Issues.
- **To implement directly**: run `/implement "description of feature"` — this works without GitHub access.
```

**Do NOT proceed to Execution.**

---

## Execution

**Only runs when `GH_AVAILABLE=true`.**

Launch a **single** product-analyst agent (`subagent_type: product-analyst`) to read and prioritize the backlog.

The product-analyst agent receives this prompt:

> You are reading the product-driven backlog from GitHub Issues and producing a prioritized view.
>
> Execute the following steps:

1. **Fetch all open product-driven backlog issues:**
   ```bash
   gh issue list --label "product-driven-backlog" --state open --limit 100 --json number,title,labels,body
   ```

2. **Parse each issue** to extract metadata from the body:
   - **Area**: from `area:*` label (e.g. `area:ui-ux` → "UI/UX")
   - **Persona Fit**: from the body's Overview table — extract `Player: X/5 · Collector: X/5 · Total: X/10`
   - **Effort**: from the body's Overview table (High/Medium/Low)
   - **Description**: from the body's "Feature Description" section
   - **User Story**: from the body's "User Story" section

   For older issues without VPC scores, infer a rough estimate:
   - Map old `Value: High` → Total ~6/10, `Value: Medium` → ~4/10, `Value: Low` → ~2/10
   - Set Player/Collector as "?" if not available

3. **Group by area** using the same label-to-name mapping as spec-backlog.

   If the user passed specific areas as input, only show those.

4. **Sort within each area by Total Persona Score (descending)**, then by Effort (Low > Medium > High) as tiebreaker.

5. **Display** as a formatted table per area, then **propose the top 3 items** for implementation:

   ```
   ## Product-Driven Backlog

   {N} open issues | Source: VPC-based product discovery
   Personas: MTG Player (Alex), MTG Collector (Morgan)

   ### {Area Name}

   | # | Issue | Player | Collector | Total | Effort |
   |---|-------|--------|-----------|-------|--------|
   | 1 | #42 Feature name | 5/5 | 3/5 | 8/10 | Low |

   (repeat for each area, sorted by Total descending)

   ---

   ## Recommended Next Sprint (Top 3)

   Ranked by VPC persona score / effort ratio (highest value, lowest effort first):

   | Priority | Issue | Area | Player | Collector | Total | Effort | Rationale |
   |----------|-------|------|--------|-----------|-------|--------|-----------|
   | 1 | #XX Feature | Area | 5/5 | 4/5 | 9/10 | Low | {why — cite specific persona pains/gains addressed} |
   | 2 | #XX Feature | Area | 4/5 | 3/5 | 7/10 | Medium | {why} |
   | 3 | #XX Feature | Area | 3/5 | 4/5 | 7/10 | Medium | {why} |

   ### Selection criteria
   - Cross-persona features (both 4+/5) prioritized over single-persona
   - Low effort preferred over high effort at same score
   - Critical pain relief weighted higher than gain creation

   Run `/implement` to start implementing these items.
   ```

5. If no issues exist, tell the user:
   ```
   No product-driven backlog issues found. Run `/update-product-driven-backlog` to generate feature ideas.
   ```
