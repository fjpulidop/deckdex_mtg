"""Configuration loader for DeckDex MTG.

This module handles loading and merging configuration from multiple sources:
1. YAML configuration files (with profile support)
2. Environment variables (DECKDEX_* prefix)
3. CLI flag overrides

Priority order (low to high): YAML → ENV → CLI
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from .config import (
    ProcessorConfig,
    ProcessingConfig,
    ScryfallConfig,
    GoogleSheetsConfig,
    OpenAIConfig,
    DatabaseConfig,
)


def load_yaml_config(config_path: Optional[str] = None, profile: str = "default") -> Dict[str, Any]:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to config file (default: config.yaml in repo root)
        profile: Profile to load (default, development, production)
        
    Returns:
        Merged configuration dictionary
    """
    # Find config file
    if config_path is None:
        # Look in current directory, then repo root
        candidates = [
            Path("config.yaml"),
            Path(__file__).parent.parent / "config.yaml"
        ]
        config_path = next((p for p in candidates if p.exists()), None)
        
        if config_path is None:
            logger.warning("No config.yaml found, using defaults")
            return {}
    
    # Load YAML
    try:
        with open(config_path, 'r') as f:
            all_configs = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config file {config_path}: {e}")
        return {}
    
    # Get default config
    config = all_configs.get("default", {})
    
    # If we need a deep copy to avoid mutation, do it here
    if config:
        import copy
        config = copy.deepcopy(config)
    
    # Merge profile if not default
    if profile != "default":
        profile_config = all_configs.get(profile)
        if profile_config is None:
            logger.warning(f"Profile '{profile}' not found in config, using default")
        else:
            config = _deep_merge(config, profile_config)
            logger.info(f"Loaded profile: {profile}")
    
    return config


def _deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        overlay: Overlay dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides.
    
    Format: DECKDEX_<SECTION>_<KEY>=value
    For nested sections: DECKDEX_GOOGLE_SHEETS_BATCH_SIZE maps to api.google_sheets.batch_size
    
    Supported patterns:
    - DECKDEX_PROCESSING_BATCH_SIZE → processing.batch_size
    - DECKDEX_SCRYFALL_MAX_RETRIES → api.scryfall.max_retries
    - DECKDEX_GOOGLE_SHEETS_BATCH_SIZE → api.google_sheets.batch_size
    - DECKDEX_OPENAI_ENABLED → api.openai.enabled
    
    Args:
        config: Configuration dictionary to update
        
    Returns:
        Updated configuration dictionary
    """
    # Map of env key prefixes to config paths
    section_mapping = {
        "processing": ["processing"],
        "scryfall": ["api", "scryfall"],
        "google_sheets": ["api", "google_sheets"],
        "openai": ["api", "openai"],
        "database": ["database"],
    }
    
    for env_key, env_value in os.environ.items():
        if not env_key.startswith("DECKDEX_"):
            continue
        
        # Parse env key (e.g., DECKDEX_PROCESSING_BATCH_SIZE or DECKDEX_GOOGLE_SHEETS_BATCH_SIZE)
        parts = env_key[8:].lower().split("_")  # Remove DECKDEX_ prefix
        if len(parts) < 2:
            continue
        
        # Determine section and key
        # Try to match known multi-word sections first
        if parts[0] == "google" and len(parts) > 2 and parts[1] == "sheets":
            section_key = "google_sheets"
            key = "_".join(parts[2:])
        else:
            section_key = parts[0]
            key = "_".join(parts[1:])
        
        # Get the config path for this section
        if section_key not in section_mapping:
            logger.debug(f"Unknown section in env var: {section_key}")
            continue
        
        config_path = section_mapping[section_key]
        
        # Convert value to appropriate type
        try:
            # Try int first
            value = int(env_value)
        except ValueError:
            try:
                # Try float
                value = float(env_value)
            except ValueError:
                # Try bool
                if env_value.lower() in ("true", "1", "yes"):
                    value = True
                elif env_value.lower() in ("false", "0", "no"):
                    value = False
                else:
                    # Keep as string
                    value = env_value
        
        # Navigate to the target section and apply override
        target = config
        for path_segment in config_path:
            if path_segment not in target:
                target[path_segment] = {}
            target = target[path_segment]
        
        target[key] = value
        logger.debug(f"Applied env override: {'.'.join(config_path)}.{key} = {value}")
    
    return config


def build_processor_config(
    yaml_config: Dict[str, Any],
    cli_overrides: Optional[Dict[str, Any]] = None,
    credentials_path: Optional[str] = None,
    update_prices: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    limit: Optional[int] = None,
    resume_from: Optional[int] = None
) -> ProcessorConfig:
    """Build ProcessorConfig from merged sources.
    
    Priority (low to high):
    1. YAML config
    2. Environment variables (already applied)
    3. CLI overrides
    
    Args:
        yaml_config: Configuration from YAML (with env overrides already applied)
        cli_overrides: Dictionary of CLI flag overrides
        credentials_path: Path to Google API credentials
        update_prices: Update prices mode flag
        dry_run: Dry run mode flag
        verbose: Verbose logging flag
        limit: Limit number of cards to process
        resume_from: Resume from specific row
        
    Returns:
        ProcessorConfig instance with nested configurations
    """
    # Extract nested configs
    processing_cfg = yaml_config.get("processing", {})
    api_cfg = yaml_config.get("api", {})
    scryfall_cfg = api_cfg.get("scryfall", {})
    sheets_cfg = api_cfg.get("google_sheets", {})
    openai_cfg = api_cfg.get("openai", {})
    database_cfg = yaml_config.get("database", {}).copy()

    # Database URL: YAML or DATABASE_URL env (standard name, no DECKDEX_ prefix)
    if os.getenv("DATABASE_URL"):
        database_cfg["url"] = os.getenv("DATABASE_URL")

    # Apply CLI overrides if provided
    if cli_overrides:
        processing_cfg.update(cli_overrides.get("processing", {}))
        scryfall_cfg.update(cli_overrides.get("scryfall", {}))
        sheets_cfg.update(cli_overrides.get("google_sheets", {}))
        openai_cfg.update(cli_overrides.get("openai", {}))
        database_cfg.update(cli_overrides.get("database", {}))

    # Build nested config objects
    processing = ProcessingConfig(**processing_cfg)
    scryfall = ScryfallConfig(**scryfall_cfg)
    google_sheets = GoogleSheetsConfig(**sheets_cfg)
    openai = OpenAIConfig(**openai_cfg)
    database = DatabaseConfig(**database_cfg) if database_cfg.get("url") else None

    # Build main config
    return ProcessorConfig(
        processing=processing,
        scryfall=scryfall,
        google_sheets=google_sheets,
        openai=openai,
        database=database,
        credentials_path=credentials_path,
        update_prices=update_prices,
        dry_run=dry_run,
        verbose=verbose,
        limit=limit,
        resume_from=resume_from
    )


def load_config(
    profile: str = "default",
    config_path: Optional[str] = None,
    **kwargs
) -> ProcessorConfig:
    """Main entry point for loading configuration.
    
    This function orchestrates the complete configuration loading pipeline:
    1. Load YAML configuration file
    2. Apply environment variable overrides (DECKDEX_*)
    3. Build ProcessorConfig with CLI overrides
    
    Args:
        profile: Configuration profile to load (default, development, production)
        config_path: Path to YAML config file (default: config.yaml in repo root)
        **kwargs: Additional arguments passed to build_processor_config
            - cli_overrides: Dict of CLI flag overrides
            - credentials_path: Path to Google API credentials
            - update_prices: Update prices mode flag
            - dry_run: Dry run mode flag
            - verbose: Verbose logging flag
            - limit: Limit number of cards
            - resume_from: Resume from row number
        
    Returns:
        Fully configured ProcessorConfig instance
        
    Example:
        >>> config = load_config(profile="production", dry_run=True)
        >>> processor = MagicCardProcessor(config)
    """
    # Load YAML
    yaml_config = load_yaml_config(config_path, profile)
    
    # Apply environment overrides
    yaml_config = apply_env_overrides(yaml_config)
    
    # Build final config
    return build_processor_config(yaml_config, **kwargs)
