"""ImporterService: Scryfall-enriched async collection importer."""

import asyncio
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deckdex.importers.base import ParsedCard
from deckdex.config_loader import load_config


class ImporterService:
    """Enriches a list of ParsedCards via Scryfall and writes them to the repository.

    Modes:
        merge  — upsert: add quantities to existing (user_id, name, set_id) rows.
        replace — delete all user's cards then bulk-insert.
    """

    def __init__(
        self,
        repo,
        user_id: int,
        mode: str = "merge",
        progress_callback: Optional[Callable] = None,
        job_repo=None,
        job_id: Optional[str] = None,
    ):
        self._repo = repo
        self._user_id = user_id
        self._mode = mode
        self._progress_callback = progress_callback
        self._job_repo = job_repo
        self._job_id = job_id
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _emit(self, current: int, total: int) -> None:
        pct = (current / total * 100) if total else 0
        if self._loop and self._progress_callback:
            asyncio.run_coroutine_threadsafe(
                self._progress_callback({
                    "type": "progress",
                    "job_id": self._job_id,
                    "current": current,
                    "total": total,
                    "percentage": pct,
                }),
                self._loop,
            )

    def _run_import(self, parsed_cards: List[ParsedCard]) -> Dict[str, Any]:
        """Runs in a thread: enrich cards then write to DB.

        Catalog-first: tries to enrich from the local catalog before falling
        back to Scryfall (only when the user has Scryfall enabled).
        """
        from deckdex.card_fetcher import CardFetcher
        from sqlalchemy import text
        from ..dependencies import get_catalog_repo, get_user_settings_repo

        config = load_config(profile=os.getenv("DECKDEX_PROFILE", "default"))
        fetcher = CardFetcher(config)

        # Resolve catalog and user settings once at the start
        catalog_repo = get_catalog_repo()
        scryfall_enabled = False
        settings_repo = get_user_settings_repo()
        if settings_repo is not None:
            user_settings = settings_repo.get_external_apis_settings(self._user_id)
            scryfall_enabled = user_settings.get("scryfall_enabled", False)

        total = len(parsed_cards)
        imported = 0
        skipped = 0
        not_found: List[str] = []
        enriched_cards: List[Dict[str, Any]] = []

        for i, pc in enumerate(parsed_cards):
            self._emit(i, total)
            card_data = None

            # 1. Try catalog first
            if catalog_repo is not None:
                try:
                    results = catalog_repo.search_by_name(pc["name"], limit=1)
                    if results:
                        card_data = results[0]
                except Exception:
                    pass

            # 2. Scryfall fallback
            if card_data is None and scryfall_enabled:
                try:
                    card_data = fetcher.search_card(pc["name"])
                except Exception:
                    pass

            if card_data is not None:
                card_data["quantity"] = pc["quantity"]
                enriched_cards.append(card_data)
            else:
                not_found.append(pc["name"])

        self._emit(total, total)

        if self._mode == "replace":
            self._repo.replace_all(enriched_cards, user_id=self._user_id)
            imported = len(enriched_cards)
            skipped = len(not_found)
        else:
            # merge: upsert per card
            engine = self._repo._get_engine()
            with engine.connect() as conn:
                for card in enriched_cards:
                    from deckdex.storage.repository import _card_to_row
                    row = _card_to_row(card)
                    name = row.get("name") or ""
                    set_id = row.get("set_id") or ""
                    qty = int(card.get("quantity") or 1)
                    if not name:
                        skipped += 1
                        continue

                    existing = conn.execute(
                        text("""
                            SELECT id, quantity FROM cards
                            WHERE user_id = :uid AND name = :name AND COALESCE(set_id,'') = :set_id
                            LIMIT 1
                        """),
                        {"uid": self._user_id, "name": name, "set_id": set_id},
                    ).fetchone()

                    if existing:
                        conn.execute(
                            text("UPDATE cards SET quantity = quantity + :qty, updated_at = NOW() AT TIME ZONE 'utc' WHERE id = :id"),
                            {"qty": qty, "id": existing[0]},
                        )
                    else:
                        cols = [k for k, v in row.items() if v is not None]
                        cols.append("user_id")
                        params = {k: row[k] for k in cols if k in row}
                        params["user_id"] = self._user_id
                        names_sql = ", ".join(cols)
                        placeholders_sql = ", ".join(f":{k}" for k in cols)
                        conn.execute(
                            text(f"INSERT INTO cards ({names_sql}) VALUES ({placeholders_sql})"),
                            params,
                        )
                    imported += 1
                conn.commit()
            skipped = len(not_found)

        result = {
            "imported": imported,
            "skipped": skipped,
            "not_found": not_found[:50],
            "mode": self._mode,
        }

        if self._job_repo and self._job_id:
            try:
                self._job_repo.update_job_status(self._job_id, "complete", result)
            except Exception as e:
                logger.warning(f"Failed to persist import job end: {e}")

        return result

    async def run_async(self, parsed_cards: List[ParsedCard]) -> Dict[str, Any]:
        """Launch import in a thread pool, emit WebSocket progress."""
        self._loop = asyncio.get_event_loop()

        if self._job_repo and self._job_id:
            try:
                self._job_repo.create_job(self._user_id, "import", job_id=self._job_id)
            except Exception as e:
                logger.warning(f"Failed to persist import job start: {e}")

        executor = ThreadPoolExecutor(max_workers=1)
        try:
            result = await self._loop.run_in_executor(executor, self._run_import, parsed_cards)
            if self._progress_callback:
                await self._progress_callback({
                    "type": "complete",
                    "job_id": self._job_id,
                    "status": "complete",
                    "summary": result,
                })
            return result
        except Exception as e:
            logger.error(f"ImporterService error: {e}")
            err_result = {"status": "error", "error": str(e)}
            if self._job_repo and self._job_id:
                try:
                    self._job_repo.update_job_status(self._job_id, "error", err_result)
                except Exception:
                    pass
            if self._progress_callback:
                await self._progress_callback({
                    "type": "complete",
                    "job_id": self._job_id,
                    "status": "error",
                    "summary": err_result,
                })
            raise
