import argparse
import sys
from deckdex.magic_card_processor import MagicCardProcessor
from deckdex.config import ProcessorConfig
from deckdex.config_loader import load_config
from deckdex.logger_config import configure_logging


def display_config(config: ProcessorConfig):
    """Display resolved configuration.
    
    Args:
        config: ProcessorConfig instance
    """
    print("\n" + "="*70)
    print("                 RESOLVED CONFIGURATION")
    print("="*70)
    print("\n## Processing")
    print(f"  batch_size: {config.processing.batch_size}")
    print(f"  max_workers: {config.processing.max_workers}")
    print(f"  api_delay: {config.processing.api_delay}s")
    print(f"  write_buffer_batches: {config.processing.write_buffer_batches}")
    
    print("\n## API: Scryfall")
    print(f"  max_retries: {config.scryfall.max_retries}")
    print(f"  retry_delay: {config.scryfall.retry_delay}s")
    print(f"  timeout: {config.scryfall.timeout}s")
    
    print("\n## API: Google Sheets")
    print(f"  batch_size: {config.google_sheets.batch_size}")
    print(f"  max_retries: {config.google_sheets.max_retries}")
    print(f"  retry_delay: {config.google_sheets.retry_delay}s")
    print(f"  sheet_name: {config.google_sheets.sheet_name}")
    print(f"  worksheet_name: {config.google_sheets.worksheet_name}")
    
    print("\n## API: OpenAI")
    print(f"  enabled: {config.openai.enabled}")
    print(f"  model: {config.openai.model}")
    print(f"  max_tokens: {config.openai.max_tokens}")
    print(f"  temperature: {config.openai.temperature}")
    print(f"  max_retries: {config.openai.max_retries}")
    
    print("\n## Behavioral Flags")
    print(f"  update_prices: {config.update_prices}")
    print(f"  dry_run: {config.dry_run}")
    print(f"  verbose: {config.verbose}")
    
    print("\n## Processing Control")
    print(f"  limit: {config.limit}")
    print(f"  resume_from: {config.resume_from}")
    print(f"  credentials_path: {config.credentials_path or '(from env)'}")
    
    print("="*70 + "\n")


def display_dry_run_banner(config: ProcessorConfig):
    """Display dry-run mode banner with configuration summary.
    
    Args:
        config: ProcessorConfig instance
    """
    print("\n" + "="*70)
    print("                    DRY RUN MODE")
    print("              No changes will be written")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  Spreadsheet: {config.sheet_name} / {config.worksheet_name}")
    print(f"  Use OpenAI: {'Yes' if config.use_openai else 'No'}")
    print(f"  Update Prices: {'Yes' if config.update_prices else 'No'}")
    print(f"  Batch Size: {config.batch_size}")
    print(f"  Workers: {config.max_workers}")
    print(f"  API Delay: {config.api_delay}s")
    print(f"  Max Retries: {config.max_retries}")
    if config.limit:
        print(f"  Limit: {config.limit} cards")
    if config.resume_from:
        print(f"  Resume From: Row {config.resume_from}")
    print("="*70 + "\n")


def get_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="DeckDex MTG - Magic card data processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python main.py
  python main.py --use_openai
  
  # Use configuration profiles
  python main.py --profile development
  python main.py --profile production
  python main.py --config custom.yaml --profile production
  
  # Performance tuning
  python main.py --workers 8 --batch-size 50
  python main.py --profile production --batch-size 100
  
  # Testing & debugging
  python main.py --dry-run --verbose
  python main.py --limit 10 --verbose
  python main.py --show-config
  python main.py --profile production --show-config
  
  # Resume from specific row
  python main.py --resume-from 100
  
  # Custom configuration
  python main.py --sheet-name "my_cards" --credentials-path "/path/to/creds.json"

Configuration priority (low to high):
  1. YAML config file (config.yaml)
  2. Environment variables (DECKDEX_*)
  3. CLI flags (highest priority)
        """
    )

    # Configuration management flags
    parser.add_argument(
        "--profile",
        type=str,
        default="default",
        help="Configuration profile to use (default, development, production)",
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        type=str,
        help="Path to configuration YAML file (default: config.yaml)",
    )
    parser.add_argument(
        "--show-config",
        dest="show_config",
        action="store_true",
        help="Display resolved configuration and exit",
    )

    # Behavioral flags
    parser.add_argument(
        "--use_openai",
        dest="use_openai",
        action="store_true",
        help="Use OpenAI to fill in the Game Strategy and Tier columns",
    )
    parser.add_argument(
        "--update_prices",
        dest="update_prices",
        action="store_true",
        help="Update all prices in the Google Sheet",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Simulate execution without writing to Google Sheets",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Enable verbose logging with detailed output",
    )
    
    # Performance settings
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of cards to process per batch (default: 20)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (1-10, default: 4)",
    )
    parser.add_argument(
        "--api-delay",
        type=float,
        default=0.1,
        help="Delay between API requests in seconds (default: 0.1)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=5,
        help="Maximum retry attempts for failed requests (default: 5)",
    )
    
    # Google Sheets configuration
    parser.add_argument(
        "--credentials-path",
        type=str,
        help="Path to Google API credentials file (overrides GOOGLE_API_CREDENTIALS env var)",
    )
    parser.add_argument(
        "--sheet-name",
        type=str,
        default="magic",
        help="Name of the Google spreadsheet (default: 'magic')",
    )
    parser.add_argument(
        "--worksheet-name",
        type=str,
        default="cards",
        help="Name of the worksheet within the spreadsheet (default: 'cards')",
    )
    
    # Processing control
    parser.add_argument(
        "--limit",
        type=int,
        help="Process only N cards (useful for testing)",
    )
    parser.add_argument(
        "--resume-from",
        type=int,
        help="Resume processing from row N (1-indexed)",
    )

    parser.set_defaults(use_openai=False, update_prices=False)

    return parser.parse_args()


def main():
    """
    Main function that starts the card data processing.
    """
    args = get_args()
    
    # Configure logging based on verbose flag
    configure_logging(args.verbose)
    
    try:
        # Build CLI overrides dictionary for parameters that can override config
        cli_overrides = {}
        
        # Check which CLI args were explicitly provided (not defaults)
        # For performance settings, build overrides dict
        if args.batch_size != 20:  # Not default
            if "processing" not in cli_overrides:
                cli_overrides["processing"] = {}
            cli_overrides["processing"]["batch_size"] = args.batch_size
        
        if args.workers != 4:  # Not default
            if "processing" not in cli_overrides:
                cli_overrides["processing"] = {}
            cli_overrides["processing"]["max_workers"] = args.workers
        
        if args.api_delay != 0.1:  # Not default
            if "processing" not in cli_overrides:
                cli_overrides["processing"] = {}
            cli_overrides["processing"]["api_delay"] = args.api_delay
        
        if args.max_retries != 5:  # Not default
            if "scryfall" not in cli_overrides:
                cli_overrides["scryfall"] = {}
            cli_overrides["scryfall"]["max_retries"] = args.max_retries
        
        # For Google Sheets settings
        if args.sheet_name != "magic":  # Not default
            if "google_sheets" not in cli_overrides:
                cli_overrides["google_sheets"] = {}
            cli_overrides["google_sheets"]["sheet_name"] = args.sheet_name
        
        if args.worksheet_name != "cards":  # Not default
            if "google_sheets" not in cli_overrides:
                cli_overrides["google_sheets"] = {}
            cli_overrides["google_sheets"]["worksheet_name"] = args.worksheet_name
        
        # For OpenAI settings
        if args.use_openai:
            if "openai" not in cli_overrides:
                cli_overrides["openai"] = {}
            cli_overrides["openai"]["enabled"] = True
        
        # Load configuration using config_loader
        config = load_config(
            profile=args.profile,
            config_path=args.config_path,
            cli_overrides=cli_overrides if cli_overrides else None,
            credentials_path=args.credentials_path,
            update_prices=args.update_prices,
            dry_run=args.dry_run,
            verbose=args.verbose,
            limit=args.limit,
            resume_from=args.resume_from,
        )
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Handle --show-config flag
    if args.show_config:
        display_config(config)
        sys.exit(0)
    
    # Display dry-run banner if applicable
    if config.dry_run:
        display_dry_run_banner(config)
    
    # Create processor and run
    processor = MagicCardProcessor(config)
    processor.process_card_data()
    
    # Display dry-run summary if applicable
    if config.dry_run and hasattr(processor.spreadsheet_client, 'display_summary'):
        processor.spreadsheet_client.display_summary()



if __name__ == "__main__":
    main()
