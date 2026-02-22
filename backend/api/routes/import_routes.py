"""
Import routes: import collection from file (CSV or JSON).
"""
import csv
import io
import json
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends

from ..dependencies import get_collection_repo, clear_collection_cache, get_current_user_id

router_import = APIRouter(prefix="/api/import", tags=["import"])


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
