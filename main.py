import argparse
import sys
from deckdex.magic_card_processor import MagicCardProcessor
from deckdex.config import ProcessorConfig
from deckdex.logger_config import configure_logging


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
  
  # Performance tuning
  python main.py --workers 8 --batch-size 50
  
  # Testing & debugging
  python main.py --dry-run --verbose
  python main.py --limit 10 --verbose
  
  # Resume from specific row
  python main.py --resume-from 100
  
  # Custom configuration
  python main.py --sheet-name "my_cards" --credentials-path "/path/to/creds.json"
        """
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
        # Create configuration from arguments
        config = ProcessorConfig(
            use_openai=args.use_openai,
            update_prices=args.update_prices,
            dry_run=args.dry_run,
            verbose=args.verbose,
            batch_size=args.batch_size,
            max_workers=args.workers,
            api_delay=args.api_delay,
            max_retries=args.max_retries,
            credentials_path=args.credentials_path,
            sheet_name=args.sheet_name,
            worksheet_name=args.worksheet_name,
            limit=args.limit,
            resume_from=args.resume_from,
        )
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    
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
