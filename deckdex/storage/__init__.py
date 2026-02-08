"""Storage layer: collection repository interface and Postgres implementation."""

from typing import Optional

from .repository import CollectionRepository, PostgresCollectionRepository

__all__ = ["CollectionRepository", "PostgresCollectionRepository", "get_collection_repository"]


def get_collection_repository(database_url: Optional[str]) -> Optional[CollectionRepository]:
    """Create a PostgresCollectionRepository if database_url is set, else None."""
    if not database_url or not database_url.strip().startswith("postgresql"):
        return None
    return PostgresCollectionRepository(database_url)
