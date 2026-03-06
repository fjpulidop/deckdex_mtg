"""ResolveService: resolve parsed card names against catalog and Scryfall."""

import os
import sys
from typing import Any, Dict, List

from loguru import logger

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deckdex.importers.base import ParsedCard

SCRYFALL_LOOKUP_CAP = 50


class ResolveService:
    """Resolve a list of ParsedCards against catalog (exact/fuzzy) and Scryfall autocomplete.

    Returns a list of dicts with resolution status and suggestions per card.
    """

    def __init__(
        self,
        catalog_repo,
        card_fetcher,
        scryfall_enabled: bool = False,
    ):
        self._catalog = catalog_repo
        self._fetcher = card_fetcher
        self._scryfall_enabled = scryfall_enabled

    def resolve(self, parsed_cards: List[ParsedCard]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        scryfall_lookups = 0

        for pc in parsed_cards:
            name = pc["name"]
            entry: Dict[str, Any] = {
                "original_name": name,
                "quantity": pc["quantity"],
                "set_name": pc.get("set_name"),
                "status": "not_found",
                "resolved_name": None,
                "suggestions": [],
            }

            # 1. Exact match in catalog
            if self._catalog is not None:
                try:
                    rows = self._catalog.search_by_name(name, limit=5)
                    exact = [r for r in rows if r["name"].lower() == name.lower()]
                    if exact:
                        entry["status"] = "matched"
                        entry["resolved_name"] = exact[0]["name"]
                        results.append(entry)
                        continue

                    # 2. Fuzzy catalog matches as suggestions
                    if rows:
                        entry["status"] = "suggested"
                        entry["suggestions"] = [r["name"] for r in rows[:3]]
                        results.append(entry)
                        continue
                except Exception as e:
                    logger.warning(f"Catalog lookup failed for '{name}': {e}")

            # 3. Scryfall autocomplete fallback
            if self._scryfall_enabled and self._fetcher and scryfall_lookups < SCRYFALL_LOOKUP_CAP:
                scryfall_lookups += 1
                try:
                    suggestions = self._fetcher.autocomplete(name)
                    if suggestions:
                        # Check if first suggestion is an exact match
                        if suggestions[0].lower() == name.lower():
                            entry["status"] = "matched"
                            entry["resolved_name"] = suggestions[0]
                        else:
                            entry["status"] = "suggested"
                            entry["suggestions"] = suggestions[:3]
                        results.append(entry)
                        continue
                except Exception as e:
                    logger.warning(f"Scryfall autocomplete failed for '{name}': {e}")

            results.append(entry)

        return results
