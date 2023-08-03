import os
import time
from dotenv import load_dotenv
from .card_fetcher import CardFetcher
from .spreadsheet_client import SpreadsheetClient
import gspread
from datetime import datetime
from tqdm import tqdm
from loguru import logger


class MagicCardProcessor:
    def __init__(self, use_openai, update_prices):
        self.use_openai = use_openai
        self.update_prices = update_prices

        # Load environment variables from .env file
        load_dotenv()

        credential_file_path = os.getenv("GOOGLE_API_CREDENTIALS")

        # Create clients
        self.card_fetcher = CardFetcher()
        self.spreadsheet_client = SpreadsheetClient(
            credential_file_path, "magic", "cards"
        )

    def update_prices_data(self, cards):
        updated_data = []
        logger.info(
            "Getting latest prices from scryfall API for all cards. If your card library is huge, it will take some time."
        )
        logger.info(
            "Please, do not execute any action on the Google Sheet until the process finish."
        )
        current_time = datetime.now().time()
        logger.info(f"Start time: {current_time.strftime('%H:%M:%S')}")
        for card in tqdm(cards):
            # fetch new data from scryfall
            new_data = self.card_fetcher.search_card(card[0])
            if new_data.get("prices", {}).get("eur") is not None:
                updated_data.append(
                    str.replace(new_data.get("prices", {}).get("eur"), ".", ",")
                )
            else:
                logger.info(
                    f"The price cannot be updated. The price card {card[0]} does not exist in scryfall api or is wrong typed."
                )
                updated_data.append("N/A")

            # Wait for 50ms to avoid overloading the Scryfall API
            time.sleep(0.05)

        current_time = datetime.now().time()
        logger.info(f"End time: {current_time.strftime('%H:%M:%S')}")
        logger.info("All cards from scryfall were fetched.")
        # Update the column in the Google Sheet
        self.spreadsheet_client.update_column("Price", updated_data)

    def process_cards(self, cards):
        card_data = []
        cell_values = []
        range_end = 1

        row_index_to_start = self.spreadsheet_client.get_empty_row_index_to_start(2)

        # Iterate over the cards and append the required information.
        for i, card in enumerate(cards, start=1):
            if i != 0 and i >= row_index_to_start:
                logger.info(f"Processing card: {card[0]}")

                # First scryfall api call. Search the english card name. The english language contains more info about the cards like the price.
                data = self.card_fetcher.search_card(card[0])

                # This will call the scryfall api again, but this time with the english card name.
                if self.use_openai:
                    if data is not None:
                        data, game_strategy, tier = self.card_fetcher.get_card_info(
                            data.get("name")
                        )
                    else:
                        logger.info(
                            "The card does not exists in scryfall api or is wrong typed."
                        )
                else:
                    if data is not None:
                        data = self.card_fetcher.search_card(data.get("name"))
                    else:
                        logger.info(
                            "The card does not exists in scryfall api or is wrong typed."
                        )
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
                        "N/A"
                        if data.get("prices", {}).get("eur") is None
                        else str.replace(data.get("prices", {}).get("eur"), ".", ","),
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
                    self.spreadsheet_client.update_cells(
                        range_start, range_end, card_data
                    )
                    logger.info(f"Updated Google Sheets with card data for {card[0]}")
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
                self.spreadsheet_client.update_cells(range_start, range_end, card_data)

            logger.info(
                "Card search has completed and results have been saved to the Google Sheets"
            )
        else:
            logger.info("Card search has completed and there are no data to update.")

    def process_card_data(self):
        if self.update_prices:
            cards = self.spreadsheet_client.get_all_cards_prices()
            self.update_prices_data(cards)
        else:
            cards = self.spreadsheet_client.get_cards()
            self.process_cards(cards)
