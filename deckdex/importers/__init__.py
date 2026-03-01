"""deckdex.importers: parsers for external MTG collection exports."""
from .base import ParsedCard, detect_format

__all__ = ["ParsedCard", "detect_format"]
