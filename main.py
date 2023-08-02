import os
import time
import logging
from dotenv import load_dotenv
from card_fetcher import CardFetcher
from spreadsheet_client import SpreadsheetClient
import gspread
import argparse

# Define your command line arguments
parser = argparse.ArgumentParser(description="Process Magic card data")
parser.add_argument(
    "--use_openai",
    dest="use_openai",
    action="store_true",
    help="Use OpenAI to fill in the Game Strategy and Tier columns",
)
parser.set_defaults(use_openai=False)

# Load environment variables from .env file
load_dotenv()

credential_file_path = os.getenv("GOOGLE_API_CREDENTIALS")

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def process_card_data(card_fetcher, spreadsheet_client, use_openai):
    """
    Process card data from a given list of cards. Fetch the information for each card,
    update the Google Sheet, and log the process.

    Parameters:
    card_fetcher (CardFetcher): An instance of CardFetcher to use to fetch card info.
    spreadsheet_client (SpreadsheetClient): An instance of SpreadsheetClient to interact with the Google Sheet.
    """
    cards = spreadsheet_client.get_cards()
    card_data = []
    cell_values = []
    range_end = 1

    row_index_to_start = spreadsheet_client.get_empty_row_index_to_start(2)

    # Iterate over the cards and append the required information.
    for i, card in enumerate(cards, start=1):
        if i != 0 and i >= row_index_to_start:
            logging.info(f"Processing card: {card[0]}")

            # First scryfall api call. Search the english card name. The english language contains more info about the cards like the price.
            data = card_fetcher.search_card(card[0])

            # This will call the scryfall api again, but this time with the english card name.
            if use_openai:
                data, game_strategy, tier = card_fetcher.get_card_info(data.get("name"))
            else:
                data = card_fetcher.search_card(data.get("name"))
                game_strategy, tier = None, None

            if data:
                cell_values = [
                    card[0],
                    data.get("name"),
                    data.get("type_line"),
                    data.get("oracle_text"),
                    str(data.get("keywords")),
                    data.get("mana_cost"),
                    data.get("cmc"),
                    str(data.get("color_identity")),
                    str(data.get("colors")),
                    data.get("power"),
                    data.get("toughness"),
                    data.get("rarity"),
                    data.get("prices", {}).get("eur"),
                    data.get("released_at"),
                    data.get("set"),
                    data.get("set_name"),
                    data.get("collector_number"),
                    data.get("edhrec_rank"),
                    game_strategy,
                    tier,
                ]
                card_data.append(cell_values)
            else:
                cell_values = [card[0]] + ["N/A"] * 19
                card_data.append(cell_values)

            # If card_data has 20 items, update Google Sheets and clear card_data
            if len(card_data) == 20:
                range_end = min(i + 1, len(cards) + 2)  # +2 because of the headers
                range_start = gspread.utils.rowcol_to_a1(
                    range_end - len(card_data), 1
                )
                range_end = gspread.utils.rowcol_to_a1(range_end, len(cell_values))
                spreadsheet_client.update_cells(range_start, range_end, card_data)
                logging.info(f"Updated Google Sheets with card data for {card[0]}")
                card_data.clear()

            # Wait for 50ms to avoid overloading the Scryfall API
            time.sleep(0.05)

    if len(cell_values) > 0:
        range_end = gspread.utils.rowcol_to_a1(range_end, len(cell_values))

        # Update Google Sheets with any remaining card data
        if card_data:
            range_end = len(cards) + 1  # +2 because of the headers
            range_start = gspread.utils.rowcol_to_a1(range_end - len(card_data), 1)
            range_end = gspread.utils.rowcol_to_a1(range_end, len(cell_values))
            spreadsheet_client.update_cells(range_start, range_end, card_data)


        logging.info(
            "Card search has completed and results have been saved to the Google Sheets"
        )
    else:
        logging.info("Card search has completed and there are no data to update.")


def main():
    """
    Main function that creates the card fetcher and spreadsheet clients and starts the card data processing.
    """
    args = parser.parse_args()
    # Create clients
    card_fetcher = CardFetcher()
    spreadsheet_client = SpreadsheetClient(credential_file_path, "magic", "cards")

    process_card_data(card_fetcher, spreadsheet_client, args.use_openai)


if __name__ == "__main__":
    main()
