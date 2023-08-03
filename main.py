import argparse
from magic_card_processor import MagicCardProcessor


def get_args():
    # Define your command line arguments
    parser = argparse.ArgumentParser(description="Process Magic card data")
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
    parser.set_defaults(use_openai=False)

    return parser.parse_args()


def main():
    """
    Main function that starts the card data processing.
    """
    args = get_args()

    processor = MagicCardProcessor(args.use_openai, args.update_prices)
    processor.process_card_data()


if __name__ == "__main__":
    main()
