# Context Bundle: Import Test Coverage Gaps

Compact reference for the developer implementing tasks.md. Read this instead of re-reading all referenced files.

---

## File: `tests/test_import_routes.py` (THE FILE TO MODIFY)

**Location**: `/Users/javi/repos/deckdex_mtg/tests/test_import_routes.py`
**Pattern**: pytest functions (not class-based), module-level sample data, single client fixture

**Relevant existing imports at module top**:
```python
import io
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app
```
`MagicMock` is already imported — no new top-level imports needed for Task 2.

**The fixture to change (Task 1)** — line 66:
```python
@pytest.fixture(scope="module")   # <-- change "module" to "function"
def import_client():
    mock_limiter = MagicMock()
    mock_limiter.limit.return_value = lambda f: f
    original_limiter = app.state.limiter
    app.state.limiter = mock_limiter
    with patch("backend.api.routes.import_routes.limiter", mock_limiter):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        client = TestClient(app)
        yield client
        app.dependency_overrides.pop(get_current_user_id, None)
    app.state.limiter = original_limiter
```

**End of file** (after line 527) is where Task 2 test function goes.

---

## File: `backend/api/services/resolve_service.py` (READ ONLY — DO NOT MODIFY)

**Location**: `/Users/javi/repos/deckdex_mtg/backend/api/services/resolve_service.py`

**Key constants and signatures**:
```python
SCRYFALL_LOOKUP_CAP = 50  # line 15

class ResolveService:
    def __init__(self, catalog_repo, card_fetcher, scryfall_enabled: bool = False):
        ...
    def resolve(self, parsed_cards: List[ParsedCard]) -> List[Dict[str, Any]]:
        ...
        scryfall_lookups = 0
        for pc in parsed_cards:
            # catalog lookup (skipped when catalog_repo is None)
            if self._scryfall_enabled and self._fetcher and scryfall_lookups < SCRYFALL_LOOKUP_CAP:
                scryfall_lookups += 1
                suggestions = self._fetcher.autocomplete(name)
                ...
```

**Import path for test**: `from backend.api.services.resolve_service import SCRYFALL_LOOKUP_CAP, ResolveService`

---

## File: `deckdex/importers/base.py` (READ ONLY — DO NOT MODIFY)

**Location**: `/Users/javi/repos/deckdex_mtg/deckdex/importers/base.py`

**ParsedCard is a TypedDict** — construct as plain dict, not constructor call:
```python
class ParsedCard(TypedDict):
    name: str
    set_name: Optional[str]
    quantity: int
```
Correct usage: `{"name": "Lightning Bolt", "quantity": 1, "set_name": None}`
Wrong usage: `ParsedCard(name="...", ...)` — TypedDict cannot be instantiated like a class.

**Import path**: `from deckdex.importers.base import ParsedCard`

---

## Project Convention: Fixture Scope

All route test fixtures in this project use `scope="function"`:
- `conftest.py`: `@pytest.fixture(scope="function") def client()`
- `test_decks.py`: `@pytest.fixture(scope="function") def deck_client()`
- `test_admin_routes.py`: three fixtures, all `scope="function"`
- `test_insights_routes.py`: `@pytest.fixture(scope="function")`
- `test_settings_scryfall_credentials_routes.py`: `scope="function"`

`scope="module"` with MagicMock is a documented pitfall — it causes cross-test state pollution.

---

## Verify

```bash
# Run only import route tests (should be 20 after Task 2)
pytest tests/test_import_routes.py -v

# Full suite sanity check
pytest tests/ -x --tb=short
```
