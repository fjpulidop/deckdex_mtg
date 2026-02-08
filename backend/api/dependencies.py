"""
Shared utilities and dependencies for API routes
"""
import os
import sys
from typing import Optional
from functools import lru_cache
from datetime import datetime, timedelta

# Add project root to Python path to import deckdex package
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from deckdex.spreadsheet_client import SpreadsheetClient
from deckdex.config_loader import load_config
from deckdex.config import ProcessorConfig
from deckdex.storage import get_collection_repository
from deckdex.storage.repository import CollectionRepository
from loguru import logger

# Cache for collection data (used when source is Google Sheets)
_collection_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 30  # seconds
}


def get_collection_repo() -> Optional[CollectionRepository]:
    """
    Get CollectionRepository when DATABASE_URL (or config.database.url) is set; else None.
    """
    config = load_config(profile=os.getenv("DECKDEX_PROFILE", "default"))
    url = None
    if config.database is not None and getattr(config.database, "url", None):
        url = config.database.url
    if not url:
        url = os.getenv("DATABASE_URL")
    return get_collection_repository(url)

def get_spreadsheet_client() -> SpreadsheetClient:
    """
    Get configured SpreadsheetClient instance.
    Resolves credentials_path from config or GOOGLE_API_CREDENTIALS env var.
    """
    config = load_config(profile=os.getenv("DECKDEX_PROFILE", "default"))
    credentials_path = config.credentials_path or os.getenv("GOOGLE_API_CREDENTIALS")
    if not credentials_path:
        raise ValueError(
            "GOOGLE_API_CREDENTIALS environment variable not set and --credentials-path not provided. "
            "Set it in your .env file or pass it as an environment variable."
        )
    return SpreadsheetClient(
        credentials_path=credentials_path,
        config=config.google_sheets,
    )

def get_cached_collection(force_refresh: bool = False):
    """
    Get collection data. When DATABASE_URL is set, reads from Postgres (with optional TTL cache).
    Otherwise reads from Google Sheets with 30-second TTL cache.

    Args:
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        List of card data (from Postgres or Google Sheets)
    """
    repo = get_collection_repo()
    if repo is not None:
        now = datetime.now()
        if (not force_refresh and
            _collection_cache['data'] is not None and
            _collection_cache['timestamp'] is not None):
            age = (now - _collection_cache['timestamp']).total_seconds()
            if age < _collection_cache['ttl']:
                logger.debug(f"Returning cached collection data from Postgres (age: {age:.1f}s)")
                return _collection_cache['data']
        logger.info("Fetching fresh collection data from Postgres")
        collection_data = repo.get_all_cards()
        _collection_cache['data'] = collection_data
        _collection_cache['timestamp'] = now
        logger.info(f"Cached {len(collection_data)} cards from Postgres")
        return collection_data

    now = datetime.now()
    if (not force_refresh and
        _collection_cache['data'] is not None and
        _collection_cache['timestamp'] is not None):
        age = (now - _collection_cache['timestamp']).total_seconds()
        if age < _collection_cache['ttl']:
            logger.debug(f"Returning cached collection data (age: {age:.1f}s)")
            return _collection_cache['data']

    logger.info("Fetching fresh collection data from Google Sheets")
    try:
        client = get_spreadsheet_client()
        all_rows = client.get_cards()
        
        # Skip header row (first row contains column names)
        cards = all_rows[1:] if len(all_rows) > 1 else []
        
        def safe_str(row, idx):
            """Get string value from row, return None for empty/N/A."""
            if idx >= len(row):
                return None
            val = row[idx]
            if not val or val == 'N/A':
                return None
            return val
        
        def safe_float(row, idx):
            """Get float value from row, return None for non-numeric."""
            val = safe_str(row, idx)
            if val is None:
                return None
            try:
                # Handle multiple price formats (European/US with or without thousands separator)
                price_clean = str(val).strip()
                
                if ',' in price_clean and '.' in price_clean:
                    last_comma_pos = price_clean.rfind(',')
                    last_dot_pos = price_clean.rfind('.')
                    
                    if last_comma_pos > last_dot_pos:
                        # European: "1.234,56"
                        price_clean = price_clean.replace('.', '').replace(',', '.')
                    else:
                        # US: "1,234.56"
                        price_clean = price_clean.replace(',', '')
                elif ',' in price_clean:
                    # Only comma: European decimal "1234,56"
                    price_clean = price_clean.replace(',', '.')
                
                return float(price_clean)
            except (ValueError, TypeError):
                return None
        
        # Column mapping based on actual Google Sheets headers:
        # [0]  Input Name
        # [1]  English name
        # [2]  Type
        # [3]  Description
        # [4]  Keywords
        # [5]  Mana Cost
        # [6]  Cmc
        # [7]  Color Identity
        # [8]  Colors
        # [9]  Strength (power)
        # [10] Resistance (toughness)
        # [11] Rarity
        # [12] Price
        # [13] Release Date
        # [14] Set ID
        # [15] Set Name
        # [16] Number in Set
        # [17] Edhrec Rank
        # [18] Game Strategy
        # [19] Tier
        
        # Convert to dict format for easier JSON serialization
        collection_data = []
        for card in cards:
            if len(card) == 0 or not card[0]:  # Skip empty rows
                continue
            collection_data.append({
                'name': safe_str(card, 0),
                'english_name': safe_str(card, 1),
                'type': safe_str(card, 2),
                'description': safe_str(card, 3),
                'keywords': safe_str(card, 4),
                'mana_cost': safe_str(card, 5),
                'cmc': safe_float(card, 6),
                'color_identity': safe_str(card, 7),
                'colors': safe_str(card, 8),
                'power': safe_str(card, 9),
                'toughness': safe_str(card, 10),
                'rarity': safe_str(card, 11),
                'price': safe_str(card, 12),
                'release_date': safe_str(card, 13),
                'set_id': safe_str(card, 14),
                'set_name': safe_str(card, 15),
                'number': safe_str(card, 16),
                'edhrec_rank': safe_str(card, 17),
                'game_strategy': safe_str(card, 18),
                'tier': safe_str(card, 19),
            })
        
        # Update cache
        _collection_cache['data'] = collection_data
        _collection_cache['timestamp'] = now
        
        logger.info(f"Cached {len(collection_data)} cards")
        return collection_data
        
    except Exception as e:
        logger.error(f"Failed to fetch collection data: {e}")
        raise

def clear_collection_cache():
    """Clear the collection cache to force refresh on next request"""
    _collection_cache['data'] = None
    _collection_cache['timestamp'] = None
    logger.info("Collection cache cleared")
