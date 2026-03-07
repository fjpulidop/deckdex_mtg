# Consolidate Color Identity Normalization

## Summary

Consolidate duplicated color identity normalization logic from `analytics.py` and `insights_service.py` into a single shared utility module `backend/api/utils/color.py`.

## Problem

Three implementations of color identity normalization exist:
1. `backend/api/filters.py` — returns `set`, different semantics (kept as-is)
2. `backend/api/routes/analytics.py` — returns `str`, full WUBRG normalization
3. `backend/api/services/insights_service.py` — returns `str`, nearly identical to analytics.py

Constants `_VALID_COLORS`, `_COLOR_NAME_MAP` are duplicated between analytics.py and insights_service.py.

## Solution

Create `backend/api/utils/color.py` with shared constants and the canonical `normalize_color_identity` function. Update both analytics.py and insights_service.py to import from it.

## Files Changed

- **Created**: `backend/api/utils/__init__.py`
- **Created**: `backend/api/utils/color.py` — shared constants + `normalize_color_identity(raw) -> str`
- **Modified**: `backend/api/routes/analytics.py` — import from utils.color, remove local duplicates
- **Modified**: `backend/api/services/insights_service.py` — import from utils.color, remove local duplicates

## Behavior

Pure refactor — no behavior changes. Same function signature, same output for all inputs.
