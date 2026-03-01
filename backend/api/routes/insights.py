"""
Collection Insights API routes

GET  /api/insights/catalog       — Full list of available insight questions
GET  /api/insights/suggestions   — Contextual suggestion chips for current user
POST /api/insights/{insight_id}  — Execute an insight computation
"""
from fastapi import APIRouter, HTTPException, Depends, Request, status
from loguru import logger

from ..dependencies import get_cached_collection, get_current_user_id
from ..services.insights_service import (
    INSIGHTS_CATALOG,
    InsightsService,
    InsightsSuggestionEngine,
)

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/catalog")
async def insights_catalog(user_id: int = Depends(get_current_user_id)):
    """Return the full list of available insight questions with metadata."""
    return INSIGHTS_CATALOG


@router.get("/suggestions")
async def insights_suggestions(user_id: int = Depends(get_current_user_id)):
    """Return 5-6 contextually relevant insight suggestions for the user."""
    try:
        cards = get_cached_collection(user_id=user_id)
        engine = InsightsSuggestionEngine(cards)
        return engine.get_suggestions(limit=6)
    except Exception as e:
        logger.error("Error computing insight suggestions: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute suggestions") from e


@router.post("/{insight_id}")
async def execute_insight(
    insight_id: str,
    user_id: int = Depends(get_current_user_id),
):
    """Execute the specified insight computation and return a rich typed response."""
    try:
        cards = get_cached_collection(user_id=user_id)
        service = InsightsService(cards)
        result = service.execute(insight_id)
        return result
    except ValueError:
        raise HTTPException(status_code=404, detail="Insight not found")
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="Insight not yet implemented")
    except Exception as e:
        logger.error("Error executing insight '%s': %s", insight_id, e)
        raise HTTPException(status_code=500, detail="Failed to execute insight") from e
