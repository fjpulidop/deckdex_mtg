"""Unit tests for backend/api/services/new_set_poller.py.

Tests cover:
  - run_once: skips already-seen sets, processes new sets, marks seen after
    successful processing, isolates per-set exceptions.
  - _fetch_sets: filters by set_type and released_at.
  - _fetch_cards_for_set: pagination, field extraction.
  - _extract_card_fields: field mapping.
  - _upsert_catalog_cards: delegates to catalog_repo when available, falls
    back to raw SQL, skips empty cards.
  - _make_get_request: retry behaviour on ConnectionError.

All fixtures use scope="function".
HTTP calls are mocked with unittest.mock.patch("requests.get").
"""

import asyncio
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from backend.api.services.new_set_poller import NewSetPoller

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_poller(
    suggestion_repo: MagicMock | None = None,
    deck_repo: MagicMock | None = None,
    catalog_repo: MagicMock | None = None,
    engine: MagicMock | None = None,
) -> NewSetPoller:
    if suggestion_repo is None:
        suggestion_repo = MagicMock()
        suggestion_repo.get_seen_set_codes.return_value = set()
    if deck_repo is None:
        deck_repo = MagicMock()
    if engine is None:
        engine = MagicMock()
    return NewSetPoller(
        engine=engine,
        suggestion_repo=suggestion_repo,
        deck_repo=deck_repo,
        catalog_repo=catalog_repo,
    )


def _run(coro):
    """Run a coroutine synchronously in tests."""
    return asyncio.run(coro)


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _make_scryfall_set(code: str = "TST", set_type: str = "expansion", released_at: str | None = None) -> dict:
    return {
        "code": code,
        "name": f"Test Set {code}",
        "set_type": set_type,
        "released_at": released_at or _today_iso(),
    }


def _mock_requests_get_response(json_data: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# Tests: run_once — set skipping
# ---------------------------------------------------------------------------


class TestRunOnceSkipsSeen(unittest.TestCase):
    """run_once skips sets whose code is already in seen_set_codes."""

    def test_skips_all_when_all_sets_seen(self):
        suggestion_repo = MagicMock()
        suggestion_repo.get_seen_set_codes.return_value = {"TST"}

        sets_response = _mock_requests_get_response(
            {
                "data": [_make_scryfall_set("TST")],
            }
        )

        poller = _make_poller(suggestion_repo=suggestion_repo)

        with patch("requests.get", return_value=sets_response):
            result = _run(poller.run_once())

        assert result == []
        suggestion_repo.insert_seen_set.assert_not_called()

    def test_processes_only_unseen_sets(self):
        """When one set is seen and one is new, only the new one is processed."""
        suggestion_repo = MagicMock()
        suggestion_repo.get_seen_set_codes.return_value = {"OLD"}
        deck_repo = MagicMock()
        deck_repo.get_deck_with_cards.return_value = None

        sets_response = _mock_requests_get_response(
            {
                "data": [
                    _make_scryfall_set("OLD"),
                    _make_scryfall_set("NEW"),
                ],
            }
        )
        cards_response = _mock_requests_get_response({"data": [], "next_page": None})

        poller = _make_poller(suggestion_repo=suggestion_repo, deck_repo=deck_repo)

        with patch("requests.get", side_effect=[sets_response, cards_response]) as mock_get:
            with patch(
                "backend.api.services.new_set_poller.compute_suggestions_for_all_decks",
                return_value=0,
            ):
                result = _run(poller.run_once())

        assert result == ["NEW"]
        suggestion_repo.insert_seen_set.assert_called_once()
        call_kwargs = suggestion_repo.insert_seen_set.call_args[0]
        assert call_kwargs[0] == "NEW"


# ---------------------------------------------------------------------------
# Tests: run_once — processes new sets
# ---------------------------------------------------------------------------


class TestRunOnceProcessesNewSets(unittest.TestCase):
    def test_marks_set_seen_after_successful_processing(self):
        """insert_seen_set is called after suggestions are computed."""
        suggestion_repo = MagicMock()
        suggestion_repo.get_seen_set_codes.return_value = set()
        deck_repo = MagicMock()
        deck_repo.get_deck_with_cards.return_value = None

        sets_resp = _mock_requests_get_response({"data": [_make_scryfall_set("NEW")]})
        cards_resp = _mock_requests_get_response({"data": []})

        poller = _make_poller(suggestion_repo=suggestion_repo, deck_repo=deck_repo)

        with patch("requests.get", side_effect=[sets_resp, cards_resp]):
            with patch(
                "backend.api.services.new_set_poller.compute_suggestions_for_all_decks",
                return_value=3,
            ):
                result = _run(poller.run_once())

        assert result == ["NEW"]
        suggestion_repo.insert_seen_set.assert_called_once_with("NEW", "Test Set NEW", _today_iso())

    def test_returns_list_of_processed_codes(self):
        suggestion_repo = MagicMock()
        suggestion_repo.get_seen_set_codes.return_value = set()

        sets_resp = _mock_requests_get_response(
            {
                "data": [_make_scryfall_set("A"), _make_scryfall_set("B")],
            }
        )
        cards_resp_a = _mock_requests_get_response({"data": []})
        cards_resp_b = _mock_requests_get_response({"data": []})

        poller = _make_poller(suggestion_repo=suggestion_repo)

        with patch("requests.get", side_effect=[sets_resp, cards_resp_a, cards_resp_b]):
            with patch(
                "backend.api.services.new_set_poller.compute_suggestions_for_all_decks",
                return_value=0,
            ):
                result = _run(poller.run_once())

        assert set(result) == {"A", "B"}

    def test_does_not_mark_seen_if_exception_occurs(self):
        """If processing fails, the set is NOT marked as seen (will retry later)."""
        suggestion_repo = MagicMock()
        suggestion_repo.get_seen_set_codes.return_value = set()

        sets_resp = _mock_requests_get_response({"data": [_make_scryfall_set("BAD")]})
        cards_resp = _mock_requests_get_response({"data": []})

        poller = _make_poller(suggestion_repo=suggestion_repo)

        with patch("requests.get", side_effect=[sets_resp, cards_resp]):
            with patch(
                "backend.api.services.new_set_poller.compute_suggestions_for_all_decks",
                side_effect=RuntimeError("DB error"),
            ):
                result = _run(poller.run_once())

        assert result == []
        suggestion_repo.insert_seen_set.assert_not_called()

    def test_fetch_sets_failure_returns_empty_list(self):
        """If fetching sets from Scryfall fails entirely, run_once returns []."""
        import requests as req

        poller = _make_poller()

        with patch("requests.get", side_effect=req.exceptions.ConnectionError("refused")):
            result = _run(poller.run_once())

        assert result == []


# ---------------------------------------------------------------------------
# Tests: run_once — per-set isolation
# ---------------------------------------------------------------------------


class TestRunOncePerSetIsolation(unittest.TestCase):
    def test_exception_for_one_set_does_not_stop_other_sets(self):
        """An error processing set A should not prevent set B from being processed."""
        suggestion_repo = MagicMock()
        suggestion_repo.get_seen_set_codes.return_value = set()

        sets_resp = _mock_requests_get_response(
            {
                "data": [_make_scryfall_set("FAIL"), _make_scryfall_set("OK")],
            }
        )
        cards_resp_fail = _mock_requests_get_response({"data": []})
        cards_resp_ok = _mock_requests_get_response({"data": []})

        call_counter = {"count": 0}

        def compute_side_effect(**kwargs):
            call_counter["count"] += 1
            if kwargs.get("set_code") == "FAIL":
                raise RuntimeError("Forced failure for FAIL set")
            return 0

        poller = _make_poller(suggestion_repo=suggestion_repo)

        with patch("requests.get", side_effect=[sets_resp, cards_resp_fail, cards_resp_ok]):
            with patch(
                "backend.api.services.new_set_poller.compute_suggestions_for_all_decks",
                side_effect=compute_side_effect,
            ):
                result = _run(poller.run_once())

        assert "OK" in result
        assert "FAIL" not in result


# ---------------------------------------------------------------------------
# Tests: _fetch_sets — filtering
# ---------------------------------------------------------------------------


class TestFetchSets(unittest.TestCase):
    def test_filters_out_irrelevant_set_types(self):
        """Token, promo, and memorabilia sets are excluded."""
        irrelevant_types = ["token", "promo", "memorabilia", "funny", "box"]
        poller = _make_poller()

        all_sets = [_make_scryfall_set(code=f"S{i}", set_type=t) for i, t in enumerate(irrelevant_types)] + [
            _make_scryfall_set(code="EXP", set_type="expansion")
        ]

        resp = _mock_requests_get_response({"data": all_sets})

        with patch("requests.get", return_value=resp):
            result = poller._fetch_sets()

        assert len(result) == 1
        assert result[0]["code"] == "EXP"

    def test_includes_all_relevant_set_types(self):
        """expansion, core, masters, draft_innovation, and commander are all kept."""
        relevant_types = ["expansion", "core", "masters", "draft_innovation", "commander"]
        poller = _make_poller()

        all_sets = [_make_scryfall_set(code=f"S{i}", set_type=t) for i, t in enumerate(relevant_types)]
        resp = _mock_requests_get_response({"data": all_sets})

        with patch("requests.get", return_value=resp):
            result = poller._fetch_sets()

        assert len(result) == len(relevant_types)

    def test_filters_out_future_sets(self):
        """Sets with released_at in the future are excluded."""
        poller = _make_poller()

        sets = [
            {**_make_scryfall_set("FUTURE"), "released_at": "2099-01-01"},
            {**_make_scryfall_set("NOW"), "released_at": _today_iso()},
        ]
        resp = _mock_requests_get_response({"data": sets})

        with patch("requests.get", return_value=resp):
            result = poller._fetch_sets()

        codes = [s["code"] for s in result]
        assert "FUTURE" not in codes
        assert "NOW" in codes


# ---------------------------------------------------------------------------
# Tests: _fetch_cards_for_set — pagination
# ---------------------------------------------------------------------------


class TestFetchCardsForSet(unittest.TestCase):
    def test_single_page_returns_all_cards(self):
        poller = _make_poller()

        raw_card = {
            "id": "abc-001",
            "name": "Lightning Bolt",
            "mana_cost": "{R}",
            "cmc": 1.0,
            "type_line": "Instant",
            "color_identity": ["R"],
            "oracle_text": "Deals 3 damage.",
            "rarity": "common",
            "image_uris": {"normal": "https://img.example.com/bolt.jpg"},
        }
        resp = _mock_requests_get_response({"data": [raw_card]})

        with patch("requests.get", return_value=resp):
            cards = poller._fetch_cards_for_set("TST")

        assert len(cards) == 1
        assert cards[0]["scryfall_id"] == "abc-001"
        assert cards[0]["name"] == "Lightning Bolt"
        assert cards[0]["color_identity"] == "R"

    def test_pagination_follows_next_page(self):
        poller = _make_poller()

        card_a = {
            "id": "p1-001",
            "name": "Card A",
            "mana_cost": None,
            "cmc": 1.0,
            "type_line": "Instant",
            "color_identity": [],
            "oracle_text": "",
            "rarity": "common",
            "image_uris": {},
        }
        card_b = {
            "id": "p2-001",
            "name": "Card B",
            "mana_cost": None,
            "cmc": 2.0,
            "type_line": "Sorcery",
            "color_identity": [],
            "oracle_text": "",
            "rarity": "rare",
            "image_uris": {},
        }

        page1_resp = _mock_requests_get_response(
            {
                "data": [card_a],
                "next_page": "https://api.scryfall.com/cards/search?page=2",
            }
        )
        page2_resp = _mock_requests_get_response({"data": [card_b]})

        with patch("requests.get", side_effect=[page1_resp, page2_resp]):
            with patch("time.sleep"):  # suppress delay
                cards = poller._fetch_cards_for_set("TST")

        assert len(cards) == 2
        ids = {c["scryfall_id"] for c in cards}
        assert ids == {"p1-001", "p2-001"}

    def test_returns_empty_for_empty_set(self):
        poller = _make_poller()
        resp = _mock_requests_get_response({"data": []})

        with patch("requests.get", return_value=resp):
            cards = poller._fetch_cards_for_set("EMPTY")

        assert cards == []


# ---------------------------------------------------------------------------
# Tests: _extract_card_fields
# ---------------------------------------------------------------------------


class TestExtractCardFields(unittest.TestCase):
    def test_extracts_expected_fields(self):
        poller = _make_poller()
        raw = {
            "id": "xyz-001",
            "name": "Counterspell",
            "mana_cost": "{U}{U}",
            "cmc": 2.0,
            "type_line": "Instant",
            "color_identity": ["U"],
            "oracle_text": "Counter target spell.",
            "rarity": "common",
            "image_uris": {"normal": "https://img.example.com/counter.jpg"},
        }
        card = poller._extract_card_fields(raw)

        assert card["scryfall_id"] == "xyz-001"
        assert card["name"] == "Counterspell"
        assert card["mana_cost"] == "{U}{U}"
        assert card["cmc"] == 2.0
        assert card["type_line"] == "Instant"
        assert card["color_identity"] == "U"
        assert card["oracle_text"] == "Counter target spell."
        assert card["rarity"] == "common"
        assert card["image_uris"] == {"normal": "https://img.example.com/counter.jpg"}

    def test_color_identity_list_joined_with_comma(self):
        poller = _make_poller()
        raw = {"id": "bgg-001", "name": "Atraxa", "color_identity": ["B", "G", "W", "U"]}
        card = poller._extract_card_fields(raw)
        colors = set(card["color_identity"].split(","))
        assert colors == {"B", "G", "W", "U"}

    def test_empty_color_identity_becomes_empty_string(self):
        poller = _make_poller()
        raw = {"id": "c-001", "name": "Wastes", "color_identity": []}
        card = poller._extract_card_fields(raw)
        assert card["color_identity"] == ""


# ---------------------------------------------------------------------------
# Tests: _upsert_catalog_cards
# ---------------------------------------------------------------------------


class TestUpsertCatalogCards(unittest.TestCase):
    def test_delegates_to_catalog_repo_when_available(self):
        catalog_repo = MagicMock()
        catalog_repo.upsert_cards = MagicMock()
        poller = _make_poller(catalog_repo=catalog_repo)

        cards = [{"scryfall_id": "abc", "name": "Test Card"}]
        poller._upsert_catalog_cards(cards)

        catalog_repo.upsert_cards.assert_called_once_with(cards)

    def test_fallback_to_engine_when_no_catalog_repo(self):
        """When catalog_repo is None, raw SQL is used via engine."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: mock_conn
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.begin.return_value = mock_conn

        poller = _make_poller(engine=mock_engine, catalog_repo=None)

        cards = [
            {
                "scryfall_id": "abc-001",
                "name": "Test Card",
                "mana_cost": None,
                "cmc": 3.0,
                "type_line": "Creature",
                "color_identity": "B",
                "oracle_text": "",
                "rarity": "common",
                "image_uris": {"normal": "https://example.com/img.jpg"},
            }
        ]

        poller._upsert_catalog_cards(cards)
        mock_engine.begin.assert_called_once()

    def test_skips_empty_cards_list(self):
        catalog_repo = MagicMock()
        poller = _make_poller(catalog_repo=catalog_repo)
        poller._upsert_catalog_cards([])
        catalog_repo.upsert_cards.assert_not_called()

    def test_skips_cards_missing_scryfall_id_or_name(self):
        """Cards without scryfall_id or name are skipped in the raw SQL fallback."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: mock_conn
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.begin.return_value = mock_conn

        poller = _make_poller(engine=mock_engine, catalog_repo=None)

        cards = [
            {"scryfall_id": "", "name": "No ID"},
            {"scryfall_id": "abc", "name": ""},
            {
                "scryfall_id": "valid-001",
                "name": "Valid Card",
                "mana_cost": None,
                "cmc": 1.0,
                "type_line": "Instant",
                "color_identity": "R",
                "oracle_text": "",
                "rarity": "common",
                "image_uris": {},
            },
        ]

        poller._upsert_catalog_cards(cards)
        # Only the valid card should be inserted — we verify execute was called at least once
        mock_conn.execute.assert_called_once()

    def test_catalog_repo_exception_falls_back_to_engine(self):
        """If catalog_repo.upsert_cards raises, the engine fallback is used."""
        catalog_repo = MagicMock()
        catalog_repo.upsert_cards.side_effect = RuntimeError("Catalog error")

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: mock_conn
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.begin.return_value = mock_conn

        poller = _make_poller(engine=mock_engine, catalog_repo=catalog_repo)

        cards = [
            {
                "scryfall_id": "abc",
                "name": "Fallback Card",
                "mana_cost": None,
                "cmc": 1.0,
                "type_line": "Instant",
                "color_identity": "R",
                "oracle_text": "",
                "rarity": "common",
                "image_uris": {},
            }
        ]
        poller._upsert_catalog_cards(cards)

        # Engine fallback should have been used
        mock_engine.begin.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: _make_get_request — retry behaviour
# ---------------------------------------------------------------------------


class TestMakeGetRequest(unittest.TestCase):
    def test_retries_once_on_connection_error(self):
        import requests as req

        poller = _make_poller()
        good_resp = _mock_requests_get_response({"data": []})

        with patch(
            "requests.get",
            side_effect=[
                req.exceptions.ConnectionError("refused"),
                good_resp,
            ],
        ) as mock_get:
            with patch("time.sleep"):  # suppress retry sleep
                result = poller._make_get_request("https://example.com")

        assert result is good_resp
        assert mock_get.call_count == 2

    def test_raises_after_second_connection_error(self):
        import requests as req

        poller = _make_poller()

        with patch("requests.get", side_effect=req.exceptions.ConnectionError("refused")):
            with patch("time.sleep"):
                with self.assertRaises(req.exceptions.ConnectionError):
                    poller._make_get_request("https://example.com")

    def test_raises_on_http_error(self):
        import requests as req

        resp = MagicMock()
        resp.raise_for_status.side_effect = req.exceptions.HTTPError("404 Not Found")
        poller = _make_poller()

        with patch("requests.get", return_value=resp):
            with self.assertRaises(req.exceptions.HTTPError):
                poller._make_get_request("https://example.com/notfound")


if __name__ == "__main__":
    unittest.main()
