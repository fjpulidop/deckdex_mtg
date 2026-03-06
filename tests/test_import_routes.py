"""Tests for import API routes (backend/api/routes/import_routes.py).

Mocks:
- get_current_user_id via dependency_overrides (FastAPI Depends)
- get_collection_repo, get_catalog_repo, get_user_settings_repo, get_job_repo via patch
  (called directly in route bodies, not as Depends)
- deckdex parsers and services via patch

Rate limiter is disabled in the module fixture by replacing app.state.limiter with a
no-op mock so successive test requests don't trigger 429s.
"""

import io
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_CSV = b"Name,Quantity,Set Name\nLightning Bolt,4,M10\nCounterspell,2,M10\n"
SAMPLE_JSON_ARRAY = json.dumps(
    [
        {"name": "Lightning Bolt", "quantity": 4},
        {"name": "Counterspell", "quantity": 2},
    ]
).encode()
SAMPLE_MTGO_TEXT = "4 Lightning Bolt\n2 Counterspell\n"

SAMPLE_PARSED_CARDS = [
    {"name": "Lightning Bolt", "quantity": 4, "set_name": None},
    {"name": "Counterspell", "quantity": 2, "set_name": None},
]

SAMPLE_RESOLVED_CARDS = [
    {
        "original_name": "Lightning Bolt",
        "quantity": 4,
        "set_name": None,
        "status": "matched",
        "resolved_name": "Lightning Bolt",
        "suggestions": [],
    },
    {
        "original_name": "Counterspell",
        "quantity": 2,
        "set_name": None,
        "status": "matched",
        "resolved_name": "Counterspell",
        "suggestions": [],
    },
]


# ---------------------------------------------------------------------------
# Module-scoped fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def import_client():
    """TestClient with auth override and rate limiter disabled.

    Rate limiter is replaced with a pass-through mock so repeated test
    requests never trigger 429 responses.
    """
    # Disable rate limiter: replace with a mock whose .limit() returns
    # a no-op decorator so @limiter.limit("5/minute") becomes a no-op.
    mock_limiter = MagicMock()
    mock_limiter.limit.return_value = lambda f: f  # decorator passthrough

    original_limiter = app.state.limiter
    app.state.limiter = mock_limiter

    # Also patch the limiter imported directly by import_routes
    with patch("backend.api.routes.import_routes.limiter", mock_limiter):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        client = TestClient(app)
        yield client
        app.dependency_overrides.pop(get_current_user_id, None)

    app.state.limiter = original_limiter


# ---------------------------------------------------------------------------
# Helper: build a fake UploadFile-compatible tuple for TestClient multipart
# ---------------------------------------------------------------------------


def _csv_file(filename: str = "cards.csv", content: bytes = SAMPLE_CSV):
    return ("file", (filename, io.BytesIO(content), "text/csv"))


def _json_file(filename: str = "cards.json", content: bytes = SAMPLE_JSON_ARRAY):
    return ("file", (filename, io.BytesIO(content), "application/json"))


# ===========================================================================
# POST /api/import/file
# ===========================================================================


def test_import_file_csv_success(import_client):
    """Valid CSV upload with mocked repo → 200 with imported count."""
    mock_repo = MagicMock()
    mock_repo.replace_all.return_value = 2

    with patch("backend.api.routes.import_routes.get_collection_repo", return_value=mock_repo):
        response = import_client.post(
            "/api/import/file",
            files=[_csv_file()],
        )

    assert response.status_code == 200
    data = response.json()
    assert "imported" in data
    assert data["imported"] == 2
    mock_repo.replace_all.assert_called_once()


def test_import_file_json_success(import_client):
    """Valid JSON array upload with mocked repo → 200 with imported count."""
    mock_repo = MagicMock()
    mock_repo.replace_all.return_value = 2

    with patch("backend.api.routes.import_routes.get_collection_repo", return_value=mock_repo):
        response = import_client.post(
            "/api/import/file",
            files=[_json_file()],
        )

    assert response.status_code == 200
    data = response.json()
    assert "imported" in data


def test_import_file_no_file_returns_400(import_client):
    """POST with no file field → 400."""
    mock_repo = MagicMock()
    mock_repo.replace_all.return_value = 0

    with patch("backend.api.routes.import_routes.get_collection_repo", return_value=mock_repo):
        response = import_client.post("/api/import/file")

    assert response.status_code == 400


def test_import_file_no_postgres_returns_501(import_client):
    """When get_collection_repo returns None → 501."""
    with patch("backend.api.routes.import_routes.get_collection_repo", return_value=None):
        response = import_client.post(
            "/api/import/file",
            files=[_csv_file()],
        )

    assert response.status_code == 501
    assert "Postgres" in response.json()["detail"] or "DATABASE_URL" in response.json()["detail"]


def test_import_file_empty_csv_returns_400(import_client):
    """CSV with header only (no data rows) → 400."""
    mock_repo = MagicMock()
    empty_csv = b"Name,Quantity\n"

    with patch("backend.api.routes.import_routes.get_collection_repo", return_value=mock_repo):
        response = import_client.post(
            "/api/import/file",
            files=[_csv_file(content=empty_csv)],
        )

    assert response.status_code == 400


# ===========================================================================
# POST /api/import/preview
# ===========================================================================


def test_import_preview_text_success(import_client):
    """POST with MTGO-style text → 200, detected_format/card_count/sample."""
    with patch(
        "deckdex.importers.mtgo.parse",
        return_value=SAMPLE_PARSED_CARDS,
    ):
        response = import_client.post(
            "/api/import/preview",
            data={"text": SAMPLE_MTGO_TEXT},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["detected_format"] == "mtgo"
    assert data["card_count"] == 2
    assert isinstance(data["sample"], list)


def test_import_preview_file_success(import_client):
    """POST with file upload → 200, detected_format/card_count/sample."""
    with patch(
        "backend.api.routes.import_routes._parse_file",
        return_value=("generic", SAMPLE_PARSED_CARDS),
    ):
        response = import_client.post(
            "/api/import/preview",
            files=[_csv_file()],
        )

    assert response.status_code == 200
    data = response.json()
    assert "detected_format" in data
    assert "card_count" in data
    assert "sample" in data


def test_import_preview_no_input_returns_400(import_client):
    """POST with neither file nor text → 400."""
    response = import_client.post("/api/import/preview")
    assert response.status_code == 400


def test_import_preview_blank_text_no_file_returns_400(import_client):
    """POST with whitespace-only text and no file → 400."""
    with patch(
        "deckdex.importers.mtgo.parse",
        return_value=[],
    ):
        response = import_client.post(
            "/api/import/preview",
            data={"text": "   "},
        )

    # Blank text is treated as "no text" → falls through to file check → 400
    assert response.status_code == 400


# ===========================================================================
# POST /api/import/resolve
# ===========================================================================


def test_import_resolve_text_success(import_client):
    """POST with MTGO text → 200 with valid ResolveResponse shape."""
    with (
        patch(
            "deckdex.importers.mtgo.parse",
            return_value=SAMPLE_PARSED_CARDS,
        ),
        patch(
            "backend.api.routes.import_routes.get_catalog_repo",
            return_value=None,
        ),
        patch(
            "backend.api.routes.import_routes.get_user_settings_repo",
            return_value=None,
        ),
        patch(
            "backend.api.services.resolve_service.ResolveService.resolve",
            return_value=SAMPLE_RESOLVED_CARDS,
        ),
    ):
        response = import_client.post(
            "/api/import/resolve",
            data={"text": SAMPLE_MTGO_TEXT},
        )

    assert response.status_code == 200
    data = response.json()
    assert "format" in data
    assert "total" in data
    assert "matched_count" in data
    assert "unresolved_count" in data
    assert "cards" in data
    assert isinstance(data["cards"], list)
    assert data["total"] == 2


def test_import_resolve_file_success(import_client):
    """POST with file → 200 with valid ResolveResponse."""
    with (
        patch(
            "backend.api.routes.import_routes._parse_file",
            return_value=("generic", SAMPLE_PARSED_CARDS),
        ),
        patch(
            "backend.api.routes.import_routes.get_catalog_repo",
            return_value=None,
        ),
        patch(
            "backend.api.routes.import_routes.get_user_settings_repo",
            return_value=None,
        ),
        patch(
            "backend.api.services.resolve_service.ResolveService.resolve",
            return_value=SAMPLE_RESOLVED_CARDS,
        ),
    ):
        response = import_client.post(
            "/api/import/resolve",
            files=[_csv_file()],
        )

    assert response.status_code == 200
    data = response.json()
    assert "cards" in data
    assert len(data["cards"]) == 2


def test_import_resolve_no_input_returns_400(import_client):
    """POST with neither file nor text → 400."""
    response = import_client.post("/api/import/resolve")
    assert response.status_code == 400


def test_import_resolve_empty_parsed_returns_400(import_client):
    """When the parser returns an empty list → 400."""
    with patch(
        "deckdex.importers.mtgo.parse",
        return_value=[],
    ):
        response = import_client.post(
            "/api/import/resolve",
            data={"text": SAMPLE_MTGO_TEXT},
        )

    assert response.status_code == 400


# ===========================================================================
# POST /api/import/external
# ===========================================================================


def test_import_external_text_success(import_client):
    """POST with MTGO text, mocked repo → 200 with job_id."""
    mock_repo = MagicMock()

    with (
        patch(
            "backend.api.routes.import_routes.get_collection_repo",
            return_value=mock_repo,
        ),
        patch(
            "deckdex.importers.mtgo.parse",
            return_value=SAMPLE_PARSED_CARDS,
        ),
        patch(
            "backend.api.routes.import_routes.get_job_repo",
            return_value=None,
        ),
    ):
        response = import_client.post(
            "/api/import/external",
            data={"text": SAMPLE_MTGO_TEXT, "mode": "merge"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert "card_count" in data
    assert data["card_count"] == 2
    assert "format" in data
    assert "mode" in data


def test_import_external_no_postgres_returns_501(import_client):
    """When get_collection_repo returns None → 501."""
    with patch(
        "backend.api.routes.import_routes.get_collection_repo",
        return_value=None,
    ):
        response = import_client.post(
            "/api/import/external",
            data={"text": SAMPLE_MTGO_TEXT},
        )

    assert response.status_code == 501
    assert "Postgres" in response.json()["detail"] or "DATABASE_URL" in response.json()["detail"]


def test_import_external_no_input_returns_400(import_client):
    """POST with neither file nor text → 400."""
    mock_repo = MagicMock()

    with patch(
        "backend.api.routes.import_routes.get_collection_repo",
        return_value=mock_repo,
    ):
        response = import_client.post("/api/import/external")

    assert response.status_code == 400


def test_import_external_file_success(import_client):
    """POST with file upload → 200 with job_id."""
    mock_repo = MagicMock()

    with (
        patch(
            "backend.api.routes.import_routes.get_collection_repo",
            return_value=mock_repo,
        ),
        patch(
            "backend.api.routes.import_routes._parse_file",
            return_value=("generic", SAMPLE_PARSED_CARDS),
        ),
        patch(
            "backend.api.routes.import_routes.get_job_repo",
            return_value=None,
        ),
    ):
        response = import_client.post(
            "/api/import/external",
            files=[_csv_file()],
            data={"mode": "merge"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data


# ===========================================================================
# POST /api/import/external/cards
# ===========================================================================


def test_import_external_cards_success(import_client):
    """POST JSON with cards list, mocked repo → 200 with job_id."""
    mock_repo = MagicMock()
    payload = {
        "cards": [
            {"name": "Lightning Bolt", "quantity": 4},
            {"name": "Counterspell", "quantity": 2},
        ],
        "mode": "merge",
    }

    with (
        patch(
            "backend.api.routes.import_routes.get_collection_repo",
            return_value=mock_repo,
        ),
        patch(
            "backend.api.routes.import_routes.get_job_repo",
            return_value=None,
        ),
    ):
        response = import_client.post(
            "/api/import/external/cards",
            json=payload,
        )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["card_count"] == 2
    assert data["format"] == "resolved"
    assert data["mode"] == "merge"


def test_import_external_cards_no_postgres_returns_501(import_client):
    """When get_collection_repo returns None → 501."""
    payload = {
        "cards": [{"name": "Lightning Bolt", "quantity": 1}],
    }

    with patch(
        "backend.api.routes.import_routes.get_collection_repo",
        return_value=None,
    ):
        response = import_client.post(
            "/api/import/external/cards",
            json=payload,
        )

    assert response.status_code == 501


def test_import_external_cards_empty_list_returns_400(import_client):
    """POST with empty cards list → 400."""
    mock_repo = MagicMock()
    payload = {"cards": []}

    with patch(
        "backend.api.routes.import_routes.get_collection_repo",
        return_value=mock_repo,
    ):
        response = import_client.post(
            "/api/import/external/cards",
            json=payload,
        )

    assert response.status_code == 400


def test_import_external_cards_replace_mode(import_client):
    """POST with mode=replace → 200, mode reflected in response."""
    mock_repo = MagicMock()
    payload = {
        "cards": [{"name": "Black Lotus", "quantity": 1}],
        "mode": "replace",
    }

    with (
        patch(
            "backend.api.routes.import_routes.get_collection_repo",
            return_value=mock_repo,
        ),
        patch(
            "backend.api.routes.import_routes.get_job_repo",
            return_value=None,
        ),
    ):
        response = import_client.post(
            "/api/import/external/cards",
            json=payload,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "replace"
