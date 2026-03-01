"""Configuration management for DeckDex MTG."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProcessingConfig:
    """Configuration for card processing.
    
    Attributes:
        batch_size: Number of cards to process per batch
        max_workers: Number of parallel ThreadPoolExecutor workers (1-10)
        api_delay: Delay in seconds between API requests
        write_buffer_batches: Number of batches to buffer before writing to sheets
    """
    batch_size: int = 20
    max_workers: int = 4
    api_delay: float = 0.1
    write_buffer_batches: int = 3
    
    def __post_init__(self):
        """Validate processing configuration parameters."""
        if self.batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if not (1 <= self.max_workers <= 10):
            raise ValueError("max_workers must be between 1 and 10")
        if self.api_delay < 0:
            raise ValueError("api_delay must be >= 0")
        if self.write_buffer_batches < 1:
            raise ValueError("write_buffer_batches must be >= 1")


@dataclass
class ScryfallConfig:
    """Configuration for Scryfall API.
    
    Attributes:
        max_retries: Maximum retry attempts for failed requests
        retry_delay: Base delay in seconds between retries
        timeout: Request timeout in seconds
    """
    max_retries: int = 3
    retry_delay: float = 0.5
    timeout: float = 10.0
    
    def __post_init__(self):
        """Validate Scryfall configuration parameters."""
        if self.max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be >= 0")
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")


@dataclass
class DatabaseConfig:
    """Configuration for PostgreSQL connection.

    Attributes:
        url: Full database URL (e.g. postgresql://user:password@host:5432/dbname).
            Can be set via config or DATABASE_URL env var.
    """
    url: Optional[str] = None

    def __post_init__(self):
        """Validate database configuration."""
        if self.url is not None and self.url.strip():
            if not self.url.strip().startswith("postgresql"):
                raise ValueError("database url must be a postgresql:// URL when set")


@dataclass
class GoogleSheetsConfig:
    """Configuration for Google Sheets API.
    
    Attributes:
        batch_size: Internal batch size for sheet updates
        max_retries: Maximum retry attempts for quota errors
        retry_delay: Base delay for exponential backoff
        sheet_name: Name of the Google spreadsheet
        worksheet_name: Name of the worksheet within spreadsheet
    """
    batch_size: int = 500
    max_retries: int = 5
    retry_delay: float = 2.0
    sheet_name: str = "magic"
    worksheet_name: str = "cards"
    
    def __post_init__(self):
        """Validate Google Sheets configuration parameters."""
        if self.batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if self.max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be >= 0")


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI API.
    
    Attributes:
        enabled: Enable OpenAI enrichment for game strategy and tier
        model: OpenAI model to use (e.g., gpt-3.5-turbo, gpt-4)
        max_tokens: Maximum tokens per completion
        temperature: Creativity level (0.0-1.0)
        max_retries: Maximum retry attempts for rate limits
    """
    enabled: bool = False
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 150
    temperature: float = 0.7
    max_retries: int = 3
    
    def __post_init__(self):
        """Validate OpenAI configuration parameters."""
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be > 0")
        if not (0.0 <= self.temperature <= 1.0):
            raise ValueError("temperature must be between 0.0 and 1.0")
        if self.max_retries < 1:
            raise ValueError("max_retries must be >= 1")


@dataclass
class CatalogConfig:
    """Configuration for the local card catalog.

    Attributes:
        image_dir: Directory for storing card images (relative to project root or absolute).
        bulk_data_url: Scryfall bulk data API endpoint (returns JSON with download_uri).
        image_size: Which Scryfall image size to download (small, normal, large).
    """
    image_dir: str = "data/images"
    bulk_data_url: str = "https://api.scryfall.com/bulk-data/default-cards"
    image_size: str = "normal"

    def __post_init__(self):
        if self.image_size not in ("small", "normal", "large"):
            raise ValueError("image_size must be one of: small, normal, large")


@dataclass
class ProcessorConfig:
    """Main configuration container for MagicCardProcessor.
    
    Now contains nested configs for each subsystem.
    
    Attributes:
        update_prices: Update only prices instead of full card processing
        dry_run: Simulate execution without writing to Google Sheets
        verbose: Enable detailed DEBUG-level logging
        processing: Nested configuration for card processing
        scryfall: Nested configuration for Scryfall API
        google_sheets: Nested configuration for Google Sheets API
        openai: Nested configuration for OpenAI API
        credentials_path: Path to Google API credentials JSON file
        limit: Process only N cards (useful for testing)
        resume_from: Resume processing from row N (1-indexed)
        process_scope: When running full process: "all" or "new_only" (only cards with just name, no type_line).
    """
    
    # Behavioral flags
    update_prices: bool = False
    process_scope: Optional[str] = None  # "all" | "new_only"
    dry_run: bool = False
    verbose: bool = False
    
    # Nested configurations
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    scryfall: ScryfallConfig = field(default_factory=ScryfallConfig)
    google_sheets: GoogleSheetsConfig = field(default_factory=GoogleSheetsConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    catalog: CatalogConfig = field(default_factory=CatalogConfig)
    database: Optional[DatabaseConfig] = field(default_factory=lambda: None)
    
    # Google Sheets credentials (not in YAML)
    credentials_path: Optional[str] = None
    
    # Processing control
    limit: Optional[int] = None
    resume_from: Optional[int] = None
    
    # Legacy properties for backwards compatibility (deprecated)
    @property
    def batch_size(self) -> int:
        """Deprecated: use processing.batch_size
        
        This property is maintained for backwards compatibility and will be
        removed in a future version. Use config.processing.batch_size instead.
        """
        import warnings
        warnings.warn(
            "config.batch_size is deprecated, use config.processing.batch_size instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.processing.batch_size
    
    @property
    def max_workers(self) -> int:
        """Deprecated: use processing.max_workers
        
        This property is maintained for backwards compatibility and will be
        removed in a future version. Use config.processing.max_workers instead.
        """
        import warnings
        warnings.warn(
            "config.max_workers is deprecated, use config.processing.max_workers instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.processing.max_workers
    
    @property
    def api_delay(self) -> float:
        """Deprecated: use processing.api_delay
        
        This property is maintained for backwards compatibility and will be
        removed in a future version. Use config.processing.api_delay instead.
        """
        import warnings
        warnings.warn(
            "config.api_delay is deprecated, use config.processing.api_delay instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.processing.api_delay
    
    @property
    def max_retries(self) -> int:
        """Deprecated: use scryfall.max_retries or google_sheets.max_retries
        
        This property is maintained for backwards compatibility and will be
        removed in a future version. Use config.scryfall.max_retries or
        config.google_sheets.max_retries instead, depending on context.
        """
        import warnings
        warnings.warn(
            "config.max_retries is deprecated, use config.scryfall.max_retries or config.google_sheets.max_retries instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.scryfall.max_retries
    
    @property
    def use_openai(self) -> bool:
        """Deprecated: use openai.enabled
        
        This property is maintained for backwards compatibility and will be
        removed in a future version. Use config.openai.enabled instead.
        """
        import warnings
        warnings.warn(
            "config.use_openai is deprecated, use config.openai.enabled instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.openai.enabled
    
    @property
    def sheet_name(self) -> str:
        """Deprecated: use google_sheets.sheet_name
        
        This property is maintained for backwards compatibility and will be
        removed in a future version. Use config.google_sheets.sheet_name instead.
        """
        import warnings
        warnings.warn(
            "config.sheet_name is deprecated, use config.google_sheets.sheet_name instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.google_sheets.sheet_name
    
    @property
    def worksheet_name(self) -> str:
        """Deprecated: use google_sheets.worksheet_name
        
        This property is maintained for backwards compatibility and will be
        removed in a future version. Use config.google_sheets.worksheet_name instead.
        """
        import warnings
        warnings.warn(
            "config.worksheet_name is deprecated, use config.google_sheets.worksheet_name instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.google_sheets.worksheet_name
    
    @property
    def write_buffer_batches(self) -> int:
        """Deprecated: use processing.write_buffer_batches
        
        This property is maintained for backwards compatibility and will be
        removed in a future version. Use config.processing.write_buffer_batches instead.
        """
        import warnings
        warnings.warn(
            "config.write_buffer_batches is deprecated, use config.processing.write_buffer_batches instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.processing.write_buffer_batches
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.limit is not None and self.limit <= 0:
            raise ValueError("limit must be > 0")
        if self.resume_from is not None and self.resume_from < 1:
            raise ValueError("resume_from must be >= 1")


class ClientFactory:
    """Factory for creating spreadsheet clients based on configuration."""
    
    @staticmethod
    def create_spreadsheet_client(config: ProcessorConfig):
        """Create appropriate spreadsheet client based on dry_run flag.
        
        Args:
            config: ProcessorConfig instance
            
        Returns:
            SpreadsheetClient if dry_run=False, DryRunClient if dry_run=True
        """
        if config.dry_run:
            from .dry_run_client import DryRunClient
            return DryRunClient(config)
        else:
            from .spreadsheet_client import SpreadsheetClient
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            credentials_path = config.credentials_path or os.getenv("GOOGLE_API_CREDENTIALS")
            if not credentials_path:
                raise ValueError(
                    "Google API credentials not configured. Set GOOGLE_API_CREDENTIALS to a valid credentials file path, "
                    "or configure credentials in Settings (Import from Google Sheets)."
                )
            if not os.path.isfile(credentials_path):
                raise ValueError(
                    f"Google API credentials file not found: {credentials_path}. "
                    "Please set GOOGLE_API_CREDENTIALS to a valid file path or configure credentials in Settings."
                )
            return SpreadsheetClient(
                credentials_path,
                config.google_sheets
            )
