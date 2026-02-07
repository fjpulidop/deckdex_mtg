"""Centralized logging configuration for DeckDex MTG."""

import sys
from loguru import logger


def configure_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level.
    
    Args:
        verbose: If True, enables DEBUG level logging with detailed output.
                If False, enables INFO level logging with concise output.
    """
    # Remove default handler
    logger.remove()
    
    # Add new handler based on verbosity
    if verbose:
        # Verbose mode: DEBUG level with detailed format
        logger.add(
            sys.stderr,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            colorize=True
        )
        logger.info("Verbose logging enabled (DEBUG level)")
    else:
        # Normal mode: INFO level with simple format
        logger.add(
            sys.stderr,
            level="INFO",
            format="<level>{message}</level>",
            colorize=True
        )
