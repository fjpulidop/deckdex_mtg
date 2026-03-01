"""Base types and format detection for collection importers."""
import csv
import io
from typing import Optional
try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class ParsedCard(TypedDict):
    name: str
    set_name: Optional[str]
    quantity: int


def detect_format(filename: str, content: str) -> str:
    """Auto-detect import format from filename and first-row headers.

    Returns one of: "moxfield", "tappedout", "mtgo", "generic".
    """
    fname = (filename or "").lower()

    # MTGO: .txt extension with no header, lines like "4 Lightning Bolt"
    if fname.endswith(".txt"):
        return "mtgo"

    # CSV: inspect headers
    try:
        reader = csv.reader(io.StringIO(content))
        headers = [h.strip().lower() for h in (next(reader, []) or [])]
    except Exception:
        headers = []

    header_set = set(headers)

    # Moxfield: "count" + "name" + "edition"
    if "count" in header_set and "name" in header_set and "edition" in header_set:
        return "moxfield"

    # TappedOut: "qty" + "name" + "set"
    if "qty" in header_set and "name" in header_set and "set" in header_set:
        return "tappedout"

    return "generic"
