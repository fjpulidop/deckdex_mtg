"""
Variant grouping service: groups user collection by card name and treatment variant.
Fetches known variant count from Scryfall prints_search_uri.
"""
from typing import Any, Dict, List, Optional

import requests
from loguru import logger

from deckdex.variant_utils import derive_variant_label

from ..dependencies import get_collection_repo


def get_collection_variants(
    user_id: int,
    search: Optional[str],
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    repo = get_collection_repo()
    if repo is None:
        raise RuntimeError("PostgreSQL required")

    names, total = repo.get_distinct_card_names(user_id, search=search, limit=limit, offset=offset)
    groups = [get_card_variants(user_id, name) for name in names]
    return {"groups": groups, "total_cards": total}


def get_card_variants(user_id: int, card_name: str) -> Dict[str, Any]:
    repo = get_collection_repo()
    if repo is None:
        raise RuntimeError("PostgreSQL required")

    owned_rows = repo.get_cards_by_name(user_id, card_name)
    if not owned_rows:
        raise ValueError(f"No cards found for name: {card_name}")

    # Build owned slots grouped by variant_label
    owned_by_label: Dict[str, List[Dict]] = {}
    scryfall_uri = None
    for row in owned_rows:
        label = row.get("variant_label") or derive_variant_label(
            row.get("finish", "nonfoil"),
            row.get("promo_types"),
            row.get("frame_effects"),
            row.get("border_color"),
        )
        owned_by_label.setdefault(label, []).append(row)
        if not scryfall_uri and row.get("scryfall_uri"):
            scryfall_uri = row["scryfall_uri"]

    # Fetch known prints from Scryfall to compute completion
    known_prints = _fetch_prints_for_card(card_name) if scryfall_uri else []

    # Build slot list: known prints + any owned labels not in Scryfall prints
    seen_labels = set()
    slots = []
    for print_obj in known_prints:
        finish = (print_obj.get("finishes") or ["nonfoil"])[0]
        pt = ",".join(print_obj.get("promo_types") or []) or None
        fe = ",".join(print_obj.get("frame_effects") or []) or None
        bc = print_obj.get("border_color")
        label = derive_variant_label(finish, pt, fe, bc)
        if label in seen_labels:
            continue
        seen_labels.add(label)
        copies = _rows_to_copies(owned_by_label.get(label, []))
        image_uri = (print_obj.get("image_uris") or {}).get("normal")
        slots.append({
            "variant_label": label,
            "finish": finish,
            "owned": bool(copies),
            "copies": copies,
            "scryfall_image_uri": image_uri,
        })

    # Append any owned labels not returned by Scryfall (edge case)
    for label, rows in owned_by_label.items():
        if label not in seen_labels:
            finish = rows[0].get("finish", "nonfoil")
            slots.append({
                "variant_label": label,
                "finish": finish,
                "owned": True,
                "copies": _rows_to_copies(rows),
                "scryfall_image_uri": None,
            })

    owned_count = sum(1 for s in slots if s["owned"])
    return {
        "card_name": card_name,
        "total_known_variants": len(slots) or len(owned_by_label),
        "owned_variant_count": owned_count,
        "slots": slots,
    }


def _rows_to_copies(rows: List[Dict]) -> List[Dict]:
    return [
        {
            "id": r["id"],
            "finish": r.get("finish", "nonfoil"),
            "variant_label": r.get("variant_label") or "Regular",
            "condition": r.get("condition"),
            "quantity": r.get("quantity", 1),
            "price": r.get("price"),
            "promo_types": r.get("promo_types"),
            "frame_effects": r.get("frame_effects"),
            "border_color": r.get("border_color"),
            "created_at": r.get("created_at"),
        }
        for r in rows
    ]


def _fetch_prints_for_card(card_name: str) -> List[Dict]:
    """
    Search Scryfall for all prints of a card name.
    Returns first page only (up to 175 prints per Scryfall page).
    On failure, returns empty list (graceful degradation).
    """
    try:
        url = f'https://api.scryfall.com/cards/search?q=!"{card_name}"&unique=prints&order=released'
        resp = requests.get(url, timeout=5, headers={"User-Agent": "DeckDex-MTG/1.0"})
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        logger.warning("Failed to fetch Scryfall prints for '{}': {}", card_name, e)
        return []
