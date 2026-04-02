"""Unit tests for backend.api.services.variant_service.

Tests cover:
- get_collection_variants: repo delegation, no-postgres error
- get_card_variants: variant label derivation, Scryfall fetch, owned/not-owned slots
- _rows_to_copies: field mapping
- _fetch_prints_for_card: HTTP success and failure

All external dependencies (get_collection_repo, requests.get) are mocked.
"""

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_row(**kwargs):
    """Build a minimal card row dict returned by repository.get_cards_by_name."""
    defaults = {
        "id": 1,
        "name": "Lightning Bolt",
        "finish": "nonfoil",
        "variant_label": None,
        "condition": "NM",
        "quantity": 1,
        "price": "0.50",
        "promo_types": None,
        "frame_effects": None,
        "border_color": None,
        "scryfall_uri": "https://scryfall.com/card/m10/lightning-bolt",
        "created_at": "2024-01-01T00:00:00",
    }
    defaults.update(kwargs)
    return defaults


def _make_scryfall_print(**kwargs):
    """Build a minimal Scryfall print object."""
    defaults = {
        "finishes": ["nonfoil"],
        "promo_types": [],
        "frame_effects": [],
        "border_color": "black",
        "image_uris": {"normal": "https://imgs.scryfall.com/card.jpg"},
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# _rows_to_copies
# ---------------------------------------------------------------------------


class TestRowsToCopies:
    """Tests for the _rows_to_copies private helper."""

    def test_empty_rows_returns_empty_list(self):
        from backend.api.services.variant_service import _rows_to_copies

        result = _rows_to_copies([])
        assert result == []

    def test_maps_all_required_fields(self):
        from backend.api.services.variant_service import _rows_to_copies

        row = _make_row(id=42, finish="foil", condition="LP", quantity=3, price="2.00")
        copies = _rows_to_copies([row])

        assert len(copies) == 1
        copy = copies[0]
        assert copy["id"] == 42
        assert copy["finish"] == "foil"
        assert copy["condition"] == "LP"
        assert copy["quantity"] == 3
        assert copy["price"] == "2.00"

    def test_variant_label_falls_back_to_regular_when_none(self):
        from backend.api.services.variant_service import _rows_to_copies

        row = _make_row(variant_label=None)
        copies = _rows_to_copies([row])
        assert copies[0]["variant_label"] == "Regular"

    def test_variant_label_used_when_present(self):
        from backend.api.services.variant_service import _rows_to_copies

        row = _make_row(variant_label="Foil")
        copies = _rows_to_copies([row])
        assert copies[0]["variant_label"] == "Foil"

    def test_quantity_defaults_to_one_when_missing(self):
        from backend.api.services.variant_service import _rows_to_copies

        row = _make_row()
        row.pop("quantity")
        copies = _rows_to_copies([row])
        assert copies[0]["quantity"] == 1

    def test_multiple_rows_produces_multiple_copies(self):
        from backend.api.services.variant_service import _rows_to_copies

        rows = [_make_row(id=1), _make_row(id=2), _make_row(id=3)]
        copies = _rows_to_copies(rows)
        assert len(copies) == 3
        assert [c["id"] for c in copies] == [1, 2, 3]


# ---------------------------------------------------------------------------
# _fetch_prints_for_card
# ---------------------------------------------------------------------------


class TestFetchPrintsForCard:
    """Tests for the _fetch_prints_for_card helper."""

    @patch("backend.api.services.variant_service.requests.get")
    def test_returns_data_list_on_success(self, mock_get):
        from backend.api.services.variant_service import _fetch_prints_for_card

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": [_make_scryfall_print()]}
        mock_get.return_value = mock_response

        result = _fetch_prints_for_card("Lightning Bolt")

        assert len(result) == 1
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert "Lightning Bolt" in call_url
        assert "unique=prints" in call_url

    @patch("backend.api.services.variant_service.requests.get")
    def test_returns_empty_list_on_http_error(self, mock_get):
        import requests

        from backend.api.services.variant_service import _fetch_prints_for_card

        mock_get.side_effect = requests.HTTPError("500 server error")
        result = _fetch_prints_for_card("Lightning Bolt")
        assert result == []

    @patch("backend.api.services.variant_service.requests.get")
    def test_returns_empty_list_on_network_timeout(self, mock_get):
        import requests

        from backend.api.services.variant_service import _fetch_prints_for_card

        mock_get.side_effect = requests.Timeout("timed out")
        result = _fetch_prints_for_card("Lightning Bolt")
        assert result == []

    @patch("backend.api.services.variant_service.requests.get")
    def test_returns_empty_list_on_json_decode_error(self, mock_get):
        from backend.api.services.variant_service import _fetch_prints_for_card

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("bad json")
        mock_get.return_value = mock_response

        result = _fetch_prints_for_card("Lightning Bolt")
        assert result == []

    @patch("backend.api.services.variant_service.requests.get")
    def test_returns_empty_list_when_data_key_missing(self, mock_get):
        from backend.api.services.variant_service import _fetch_prints_for_card

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {}  # No 'data' key
        mock_get.return_value = mock_response

        result = _fetch_prints_for_card("Lightning Bolt")
        assert result == []

    @patch("backend.api.services.variant_service.requests.get")
    def test_includes_user_agent_header(self, mock_get):
        from backend.api.services.variant_service import _fetch_prints_for_card

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        _fetch_prints_for_card("Test Card")

        # headers is passed as a keyword argument to requests.get
        kwargs = mock_get.call_args[1]
        headers = kwargs.get("headers", {})
        assert "DeckDex" in str(headers)


# ---------------------------------------------------------------------------
# get_collection_variants
# ---------------------------------------------------------------------------


class TestGetCollectionVariants:
    """Tests for get_collection_variants service function."""

    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_raises_runtime_error_when_no_postgres(self, mock_get_repo):
        """RuntimeError raised when repo is unavailable (no PostgreSQL)."""
        from backend.api.services.variant_service import get_collection_variants

        mock_get_repo.return_value = None

        with pytest.raises(RuntimeError, match="PostgreSQL required"):
            get_collection_variants(user_id=1, search=None, limit=50, offset=0)

    @patch("backend.api.services.variant_service.get_card_variants")
    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_returns_groups_and_total(self, mock_get_repo, mock_get_card_variants):
        """Returns dict with 'groups' list and 'total_cards' count."""
        from backend.api.services.variant_service import get_collection_variants

        mock_repo = MagicMock()
        mock_repo.get_distinct_card_names.return_value = (["Lightning Bolt", "Counterspell"], 2)
        mock_get_repo.return_value = mock_repo

        mock_get_card_variants.side_effect = lambda user_id, card_name: {
            "card_name": card_name,
            "total_known_variants": 1,
            "owned_variant_count": 1,
            "slots": [],
        }

        result = get_collection_variants(user_id=1, search=None, limit=50, offset=0)

        assert result["total_cards"] == 2
        assert len(result["groups"]) == 2
        assert result["groups"][0]["card_name"] == "Lightning Bolt"
        assert result["groups"][1]["card_name"] == "Counterspell"

    @patch("backend.api.services.variant_service.get_card_variants")
    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_passes_search_to_repo(self, mock_get_repo, mock_get_card_variants):
        """search parameter is forwarded to repo.get_distinct_card_names."""
        from backend.api.services.variant_service import get_collection_variants

        mock_repo = MagicMock()
        mock_repo.get_distinct_card_names.return_value = ([], 0)
        mock_get_repo.return_value = mock_repo
        mock_get_card_variants.return_value = {}

        get_collection_variants(user_id=7, search="bolt", limit=10, offset=5)

        mock_repo.get_distinct_card_names.assert_called_once_with(7, search="bolt", limit=10, offset=5)

    @patch("backend.api.services.variant_service.get_card_variants")
    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_empty_names_returns_empty_groups(self, mock_get_repo, mock_get_card_variants):
        """When no card names exist, returns empty groups list."""
        from backend.api.services.variant_service import get_collection_variants

        mock_repo = MagicMock()
        mock_repo.get_distinct_card_names.return_value = ([], 0)
        mock_get_repo.return_value = mock_repo

        result = get_collection_variants(user_id=1, search=None, limit=50, offset=0)

        assert result["groups"] == []
        assert result["total_cards"] == 0
        mock_get_card_variants.assert_not_called()


# ---------------------------------------------------------------------------
# get_card_variants
# ---------------------------------------------------------------------------


class TestGetCardVariants:
    """Tests for get_card_variants service function."""

    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_raises_runtime_error_when_no_postgres(self, mock_get_repo):
        from backend.api.services.variant_service import get_card_variants

        mock_get_repo.return_value = None
        with pytest.raises(RuntimeError, match="PostgreSQL required"):
            get_card_variants(user_id=1, card_name="Lightning Bolt")

    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_raises_value_error_when_no_rows(self, mock_get_repo):
        from backend.api.services.variant_service import get_card_variants

        mock_repo = MagicMock()
        mock_repo.get_cards_by_name.return_value = []
        mock_get_repo.return_value = mock_repo

        with pytest.raises(ValueError, match="No cards found for name"):
            get_card_variants(user_id=1, card_name="Nonexistent Card")

    @patch("backend.api.services.variant_service._fetch_prints_for_card")
    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_returns_correct_card_name(self, mock_get_repo, mock_fetch):
        from backend.api.services.variant_service import get_card_variants

        mock_repo = MagicMock()
        mock_repo.get_cards_by_name.return_value = [_make_row()]
        mock_get_repo.return_value = mock_repo
        mock_fetch.return_value = []

        result = get_card_variants(user_id=1, card_name="Lightning Bolt")
        assert result["card_name"] == "Lightning Bolt"

    @patch("backend.api.services.variant_service._fetch_prints_for_card")
    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_owned_variant_count_matches_owned_slots(self, mock_get_repo, mock_fetch):
        from backend.api.services.variant_service import get_card_variants

        mock_repo = MagicMock()
        mock_repo.get_cards_by_name.return_value = [_make_row(finish="nonfoil", variant_label="Regular")]
        mock_get_repo.return_value = mock_repo
        mock_fetch.return_value = []

        result = get_card_variants(user_id=1, card_name="Lightning Bolt")

        assert result["owned_variant_count"] == 1
        assert result["total_known_variants"] >= 1

    @patch("backend.api.services.variant_service._fetch_prints_for_card")
    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_derives_variant_label_from_finish_when_no_label(self, mock_get_repo, mock_fetch):
        """When variant_label is None in DB, it is derived from finish/frame_effects."""
        from backend.api.services.variant_service import get_card_variants

        mock_repo = MagicMock()
        mock_repo.get_cards_by_name.return_value = [
            _make_row(finish="foil", variant_label=None, frame_effects=None, promo_types=None, border_color=None)
        ]
        mock_get_repo.return_value = mock_repo
        mock_fetch.return_value = []

        result = get_card_variants(user_id=1, card_name="Lightning Bolt")

        # Should have at least one slot that is owned with label "Foil"
        owned_slots = [s for s in result["slots"] if s["owned"]]
        assert len(owned_slots) == 1
        assert owned_slots[0]["variant_label"] == "Foil"

    @patch("backend.api.services.variant_service._fetch_prints_for_card")
    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_uses_stored_variant_label_when_present(self, mock_get_repo, mock_fetch):
        """When variant_label is set in DB row, it is used directly."""
        from backend.api.services.variant_service import get_card_variants

        mock_repo = MagicMock()
        mock_repo.get_cards_by_name.return_value = [_make_row(variant_label="Extended Art")]
        mock_get_repo.return_value = mock_repo
        mock_fetch.return_value = []

        result = get_card_variants(user_id=1, card_name="Lightning Bolt")

        owned_slots = [s for s in result["slots"] if s["owned"]]
        assert any(s["variant_label"] == "Extended Art" for s in owned_slots)

    @patch("backend.api.services.variant_service._fetch_prints_for_card")
    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_scryfall_prints_create_unowned_slots(self, mock_get_repo, mock_fetch):
        """Scryfall prints not in user's collection appear as unowned slots."""
        from backend.api.services.variant_service import get_card_variants

        mock_repo = MagicMock()
        # User owns only a foil
        mock_repo.get_cards_by_name.return_value = [
            _make_row(finish="foil", variant_label="Foil", scryfall_uri="https://scryfall.com/foo")
        ]
        mock_get_repo.return_value = mock_repo

        # Scryfall says there's also a nonfoil print
        mock_fetch.return_value = [
            _make_scryfall_print(finishes=["nonfoil"], frame_effects=[], promo_types=[], border_color="black"),
            _make_scryfall_print(finishes=["foil"], frame_effects=[], promo_types=[], border_color="black"),
        ]

        result = get_card_variants(user_id=1, card_name="Lightning Bolt")

        labels = {s["variant_label"] for s in result["slots"]}
        assert "Foil" in labels
        assert "Regular" in labels

        unowned_slots = [s for s in result["slots"] if not s["owned"]]
        assert len(unowned_slots) >= 1

    @patch("backend.api.services.variant_service._fetch_prints_for_card")
    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_owned_labels_not_in_scryfall_appended(self, mock_get_repo, mock_fetch):
        """Labels owned by user but not in Scryfall prints are appended as owned slots."""
        from backend.api.services.variant_service import get_card_variants

        mock_repo = MagicMock()
        # User owns a "Serialized" variant
        mock_repo.get_cards_by_name.return_value = [
            _make_row(variant_label="Serialized", promo_types="serialized", scryfall_uri=None)
        ]
        mock_get_repo.return_value = mock_repo
        # Scryfall returns nothing (scryfall_uri is None → fetch not called)
        mock_fetch.return_value = []

        result = get_card_variants(user_id=1, card_name="Lightning Bolt")

        owned_slots = [s for s in result["slots"] if s["owned"]]
        assert len(owned_slots) >= 1

    @patch("backend.api.services.variant_service._fetch_prints_for_card")
    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_scryfall_image_uri_included_in_owned_slot(self, mock_get_repo, mock_fetch):
        """scryfall_image_uri is set on slots from Scryfall data."""
        from backend.api.services.variant_service import get_card_variants

        mock_repo = MagicMock()
        mock_repo.get_cards_by_name.return_value = [
            _make_row(finish="nonfoil", variant_label=None, scryfall_uri="https://scryfall.com/foo")
        ]
        mock_get_repo.return_value = mock_repo

        img_url = "https://imgs.scryfall.com/card-normal.jpg"
        mock_fetch.return_value = [
            _make_scryfall_print(
                finishes=["nonfoil"],
                frame_effects=[],
                promo_types=[],
                border_color="black",
                image_uris={"normal": img_url},
            )
        ]

        result = get_card_variants(user_id=1, card_name="Lightning Bolt")

        regular_slots = [s for s in result["slots"] if s["variant_label"] == "Regular"]
        assert len(regular_slots) >= 1
        assert regular_slots[0]["scryfall_image_uri"] == img_url

    @patch("backend.api.services.variant_service._fetch_prints_for_card")
    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_duplicate_labels_in_scryfall_deduplicated(self, mock_get_repo, mock_fetch):
        """Scryfall prints with the same derived label are deduplicated (one slot per label)."""
        from backend.api.services.variant_service import get_card_variants

        mock_repo = MagicMock()
        mock_repo.get_cards_by_name.return_value = [
            _make_row(finish="nonfoil", variant_label="Regular", scryfall_uri="https://scryfall.com/foo")
        ]
        mock_get_repo.return_value = mock_repo

        # Two prints that both resolve to "Regular"
        mock_fetch.return_value = [
            _make_scryfall_print(finishes=["nonfoil"], frame_effects=[], promo_types=[], border_color="black"),
            _make_scryfall_print(finishes=["nonfoil"], frame_effects=[], promo_types=[], border_color="black"),
        ]

        result = get_card_variants(user_id=1, card_name="Lightning Bolt")

        regular_count = sum(1 for s in result["slots"] if s["variant_label"] == "Regular")
        assert regular_count == 1

    @patch("backend.api.services.variant_service._fetch_prints_for_card")
    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_no_scryfall_uri_skips_fetch(self, mock_get_repo, mock_fetch):
        """When no owned card has a scryfall_uri, Scryfall fetch is not attempted."""
        from backend.api.services.variant_service import get_card_variants

        mock_repo = MagicMock()
        mock_repo.get_cards_by_name.return_value = [_make_row(scryfall_uri=None)]
        mock_get_repo.return_value = mock_repo

        get_card_variants(user_id=1, card_name="Lightning Bolt")

        mock_fetch.assert_not_called()

    @patch("backend.api.services.variant_service._fetch_prints_for_card")
    @patch("backend.api.services.variant_service.get_collection_repo")
    def test_user_id_passed_to_repo(self, mock_get_repo, mock_fetch):
        """Correct user_id is passed to repo.get_cards_by_name."""
        from backend.api.services.variant_service import get_card_variants

        mock_repo = MagicMock()
        mock_repo.get_cards_by_name.return_value = [_make_row()]
        mock_get_repo.return_value = mock_repo
        mock_fetch.return_value = []

        get_card_variants(user_id=42, card_name="Counterspell")

        mock_repo.get_cards_by_name.assert_called_once_with(42, "Counterspell")
