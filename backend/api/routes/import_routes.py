"""
Import routes: import collection from file (CSV, JSON, or external app exports).
"""
import csv
import io
import json
import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form, Depends
from loguru import logger

from ..dependencies import get_collection_repo, clear_collection_cache, get_current_user_id, get_job_repo
from ..websockets.progress import manager as ws_manager

router_import = APIRouter(prefix="/api/import", tags=["import"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_content(file_content: bytes) -> str:
    try:
        return file_content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text (CSV, JSON, or .txt).")


def _parse_file(filename: str, content: str):
    """Detect format and parse. Returns (format_name, List[ParsedCard])."""
    from deckdex.importers.base import detect_format
    from deckdex.importers import moxfield, tappedout, mtgo, generic_csv

    fmt = detect_format(filename, content)
    parsers = {
        "moxfield": moxfield.parse,
        "tappedout": tappedout.parse,
        "mtgo": mtgo.parse,
        "generic": generic_csv.parse,
    }
    cards = parsers[fmt](content)
    return fmt, cards


@router_import.post("/file")
async def import_from_file(
    file: Optional[UploadFile] = File(None),
    user_id: int = Depends(get_current_user_id)
):
    """
    Accept CSV or JSON file upload; parse and replace collection in Postgres.
    CSV: first row = header (Name, English name, Type, ... or similar). JSON: array of card objects.
    """
    repo = get_collection_repo()
    if not repo:
        raise HTTPException(status_code=501, detail="Postgres required. Set DATABASE_URL.")

    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    content = await file.read()
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text (CSV or JSON).")

    filename = (file.filename or "").lower()
    cards: List[dict] = []

    if filename.endswith(".json"):
        try:
            data = json.loads(text_content)
            if isinstance(data, list):
                cards = data
            elif isinstance(data, dict) and "cards" in data:
                cards = data["cards"]
            else:
                cards = [data]
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    else:
        # CSV (or no extension)
        reader = csv.reader(io.StringIO(text_content))
        rows = list(reader)
        if not rows:
            raise HTTPException(status_code=400, detail="CSV is empty.")
        header = [h.strip().lower() for h in rows[0]]
        name_col = None
        for i, h in enumerate(header):
            if "name" in h and (not name_col or h in ("name", "input name")):
                name_col = i
                break
        if name_col is None:
            name_col = 0
        key_map = {
            "name": "name", "input name": "name", "english name": "english_name", "type": "type",
            "description": "description", "keywords": "keywords", "mana cost": "mana_cost",
            "cmc": "cmc", "color identity": "color_identity", "colors": "colors",
            "power": "power", "strength": "power", "toughness": "toughness", "resistance": "toughness",
            "rarity": "rarity", "price": "price", "release date": "release_date",
            "set id": "set_id", "set name": "set_name", "number in set": "number", "number": "number",
            "edhrec rank": "edhrec_rank", "game strategy": "game_strategy", "tier": "tier",
        }
        for row in rows[1:]:
            if not row or not (row[name_col] or "").strip():
                continue
            card = {}
            for i, val in enumerate(row):
                if i < len(header) and val and val.strip():
                    h = header[i]
                    key = key_map.get(h, h.replace(" ", "_"))
                    card[key] = val.strip()
            if card.get("name"):
                cards.append(card)

    if not cards:
        raise HTTPException(status_code=400, detail="No valid cards in file.")
    count = repo.replace_all(cards, user_id=user_id)
    clear_collection_cache()
    return {"imported": count}


# ---------------------------------------------------------------------------
# POST /api/import/preview
# ---------------------------------------------------------------------------
@router_import.post("/preview")
async def import_preview(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    user_id: int = Depends(get_current_user_id),
):
    """Parse file or pasted text and return detected format + card count + sample (no DB writes)."""
    if text and text.strip():
        from deckdex.importers.mtgo import parse as mtgo_parse
        try:
            parsed = mtgo_parse(text)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse text: {e}")
        if not parsed:
            raise HTTPException(status_code=400, detail="No cards found in text.")
        return {
            "detected_format": "mtgo",
            "card_count": len(parsed),
            "sample": [c["name"] for c in parsed[:5]],
        }

    if not file:
        raise HTTPException(status_code=400, detail="Provide a file or paste card text.")

    content_bytes = await file.read()
    text_content = _read_content(content_bytes)
    filename = file.filename or ""

    try:
        fmt, parsed = _parse_file(filename, text_content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    if not parsed:
        raise HTTPException(status_code=400, detail="No cards found in file.")

    return {
        "detected_format": fmt,
        "card_count": len(parsed),
        "sample": [c["name"] for c in parsed[:5]],
    }


# ---------------------------------------------------------------------------
# POST /api/import/external
# ---------------------------------------------------------------------------
@router_import.post("/external")
async def import_external(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    mode: str = Form(default="merge"),
    user_id: int = Depends(get_current_user_id),
):
    """Parse external collection file or pasted text, enrich via Scryfall, write to DB as async job."""
    repo = get_collection_repo()
    if not repo:
        raise HTTPException(status_code=501, detail="Postgres required. Set DATABASE_URL.")

    if mode not in ("merge", "replace"):
        mode = "merge"

    if text and text.strip():
        from deckdex.importers.mtgo import parse as mtgo_parse
        try:
            parsed_cards = mtgo_parse(text)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse text: {e}")
        fmt = "mtgo"
    elif file:
        content_bytes = await file.read()
        text_content = _read_content(content_bytes)
        filename = file.filename or ""
        try:
            fmt, parsed_cards = _parse_file(filename, text_content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")
    else:
        raise HTTPException(status_code=400, detail="Provide a file or paste card text.")

    if not parsed_cards:
        raise HTTPException(status_code=400, detail="No cards found.")

    job_id = str(uuid.uuid4())
    job_repo = get_job_repo()

    async def progress_callback(event):
        event_type = event.get("type")
        if event_type == "progress":
            await ws_manager.send_progress(
                job_id,
                event.get("current", 0),
                event.get("total", 0),
                event.get("percentage", 0.0),
            )
        elif event_type == "complete":
            await ws_manager.send_complete(
                job_id,
                event.get("status", "complete"),
                event.get("summary", {}),
            )

    from ..services.importer_service import ImporterService
    service = ImporterService(
        repo=repo,
        user_id=user_id,
        mode=mode,
        progress_callback=progress_callback,
        job_repo=job_repo,
        job_id=job_id,
    )

    async def run_import():
        try:
            await service.run_async(parsed_cards)
            clear_collection_cache()
        except Exception as e:
            logger.error(f"Import job {job_id} failed: {e}")

    background_tasks.add_task(run_import)
    return {"job_id": job_id, "card_count": len(parsed_cards), "format": fmt, "mode": mode}
