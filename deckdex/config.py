"""Configuration management for DeckDex MTG."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProcessorConfig:
    """Configuration for MagicCardProcessor.
    
    Attributes:
        use_openai: Enable OpenAI enrichment for game strategy and tier
        update_prices: Update only prices instead of full card processing
        dry_run: Simulate execution without writing to Google Sheets
        verbose: Enable detailed DEBUG-level logging
        batch_size: Number of cards to process per batch
        max_workers: Number of parallel ThreadPoolExecutor workers
        api_delay: Delay in seconds between API requests (Scryfall rate limiting)
        max_retries: Maximum retry attempts for failed API requests
        credentials_path: Path to Google API credentials JSON file
        sheet_name: Name of the Google spreadsheet
        worksheet_name: Name of the worksheet within the spreadsheet
        limit: Process only N cards (useful for testing)
        resume_from: Resume processing from row N (1-indexed)
    """
    
    # Behavioral flags
    use_openai: bool = False
    update_prices: bool = False
    dry_run: bool = False
    verbose: bool = False
    
    # Performance settings (optimized for Scryfall 10 req/s)
    batch_size: int = 20
    max_workers: int = 4
    api_delay: float = 0.1  # 100ms = safe for 10 req/s limit
    max_retries: int = 5
    
    # Google Sheets settings
    credentials_path: Optional[str] = None
    sheet_name: str = "magic"
    worksheet_name: str = "cards"
    
    # Processing control
    limit: Optional[int] = None      # Process only N cards
    resume_from: Optional[int] = None  # Resume from row N
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if not (1 <= self.max_workers <= 10):
            raise ValueError("max_workers must be between 1 and 10")
        if self.max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        if self.api_delay < 0:
            raise ValueError("api_delay must be >= 0")
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
                raise ValueError("GOOGLE_API_CREDENTIALS environment variable not set and --credentials-path not provided")
            
            return SpreadsheetClient(
                credentials_path,
                config.sheet_name,
                config.worksheet_name
            )
