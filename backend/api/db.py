"""Shared database engine singleton.

Provides a single SQLAlchemy engine shared across all repositories,
avoiding the creation of multiple connection pools.
"""

import os
from typing import Optional

from loguru import logger

_engine = None


def get_database_url() -> Optional[str]:
    """Resolve DATABASE_URL from config or environment."""
    try:
        from deckdex.config_loader import load_config
        config = load_config(profile=os.getenv("DECKDEX_PROFILE", "default"))
        if config.database is not None and getattr(config.database, "url", None):
            return config.database.url
    except Exception:
        pass
    return os.getenv("DATABASE_URL")


def get_engine():
    """Return the shared SQLAlchemy engine, creating it on first call.

    Returns None if no DATABASE_URL is configured.
    """
    global _engine
    if _engine is not None:
        return _engine

    url = get_database_url()
    if not url or not str(url).strip().startswith("postgresql"):
        return None

    from sqlalchemy import create_engine
    _engine = create_engine(
        url,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    logger.info("Shared DB engine created (pool_size=20, max_overflow=40)")
    return _engine


def dispose_engine():
    """Dispose the shared engine (for testing/shutdown)."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
