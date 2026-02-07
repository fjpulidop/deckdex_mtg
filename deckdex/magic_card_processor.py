import os
import time
import random
from typing import List, Dict, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from dotenv import load_dotenv
from .card_fetcher import CardFetcher
from .spreadsheet_client import SpreadsheetClient
import gspread
from datetime import datetime
from tqdm import tqdm
from loguru import logger
import sys


# ANSI colors for terminal
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


class MagicCardProcessor:
    BATCH_SIZE = 20
    MAX_RETRIES = 5
    INITIAL_RETRY_DELAY = 1
    API_RATE_LIMIT_DELAY = 0.05

    def __init__(self, use_openai: bool, update_prices: bool):
        self.use_openai = use_openai
        self.update_prices = update_prices
        self._initialize_clients()
        self._card_cache = {}
        self.error_count = 0
        self.last_error_count = 0
        self.not_found_cards = []  # List to store names of cards not found

    def _initialize_clients(self) -> None:
        load_dotenv()
        credential_file_path = os.getenv("GOOGLE_API_CREDENTIALS")
        if not credential_file_path:
            raise ValueError("GOOGLE_API_CREDENTIALS environment variable not set")
        
        self.card_fetcher = CardFetcher()
        self.spreadsheet_client = SpreadsheetClient(
            credential_file_path, "magic", "cards"
        )

    @lru_cache(maxsize=1000)
    def _fetch_card_data(self, card_name: str) -> Optional[Dict[str, Any]]:
        """Fetch card data with caching."""
        try:
            return self.card_fetcher.search_card(card_name)
        except Exception as e:
            # Check if it's a 404 error (card not found)
            if "404" in str(e) or "not found" in str(e).lower():
                self.error_count += 1
                # Save the name of the card not found (limit to 100 to avoid excessive memory usage)
                if len(self.not_found_cards) < 100:
                    self.not_found_cards.append(card_name)
                # Show the error immediately
                self._print_error_counter("search")
            else:
                # Other type of error
                self.error_count += 1
            return None

    def _process_price(self, price: Optional[str]) -> str:
        """Process price value."""
        if not price:
            return "N/A"
        return str.replace(price, ".", ",")

    def _update_prices_batch(self, cards: List[List[str]], start_idx: int, batch_size: int) -> List[Tuple[int, str, str]]:
        """
        Process a batch of cards for price updates.
        
        Args:
            cards: List of [card_name, current_price] entries
            start_idx: Starting index in the cards list
            batch_size: Number of cards to process in this batch
            
        Returns:
            List of tuples (row_index, card_name, new_price) for cards with changed prices
        """
        updated_data = []
        for i, card in enumerate(cards[start_idx:start_idx + batch_size], start=start_idx):
            card_name, current_price = card
            data = self._fetch_card_data(card_name)
            new_price_raw = data.get("prices", {}).get("eur") if data else None
            new_price = self._process_price(new_price_raw)
            
            # Only include cards where the price has changed
            if new_price != current_price:
                # Row index is 0-based index + 2 (header row + 1-based indexing)
                row_index = i + 2
                updated_data.append((row_index, card_name, new_price))
            
            time.sleep(self.API_RATE_LIMIT_DELAY)
        return updated_data

    def _print_error_counter(self, phase: str = "search") -> None:
        """
        Print the error counter with highlighted formatting.
        
        Args:
            phase: Phase of the process (search or update)
        """
        if self.error_count > 0 and self.error_count != self.last_error_count:
            # Save the last displayed value to avoid unnecessary updates
            self.last_error_count = self.error_count
            
            # Create a highlighted message with colors
            error_msg = f"\n{Colors.BOLD}{Colors.RED}⚠️ Cards not found: {self.error_count} ⚠️{Colors.END}"
            
            # If we have cards not found, show the last 3
            if self.not_found_cards:
                last_cards = self.not_found_cards[-3:]
                cards_str = ", ".join([f"'{card}'" for card in last_cards])
                error_msg += f"\n{Colors.YELLOW}Last not found: {cards_str}{Colors.END}"
            
            # Print the message on a new line to make it more visible
            print(error_msg)
            
            # Force output to ensure it displays immediately
            sys.stdout.flush()

    def update_prices_data(self, cards: List[List[str]]) -> None:
        """
        Update prices with parallel processing, but only for cards where prices have changed.
        
        Args:
            cards: List of [card_name, current_price] entries
        """
        logger.info("Checking price updates from Scryfall API...")
        start_time = datetime.now()
        
        # Reset the error counter and the list of cards not found
        self.error_count = 0
        self.last_error_count = 0
        self.not_found_cards = []
        changed_prices = []
        total_cards = len(cards)
        
        # Print an initial message for the error counter
        print(f"{Colors.BOLD}Cards not found counter: {self.error_count}{Colors.END}")
        
        # Configure tqdm to show only the progress bar with time estimation
        with tqdm(total=total_cards, desc="Verifying prices", unit="cards") as pbar:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for i in range(0, len(cards), self.BATCH_SIZE):
                    futures.append(
                        executor.submit(self._update_prices_batch, cards, i, self.BATCH_SIZE)
                    )
                
                for future in futures:
                    batch_results = future.result()
                    changed_prices.extend(batch_results)
                    # Update the progress bar with the processed batch size
                    pbar.update(min(self.BATCH_SIZE, total_cards - pbar.n))
                    
                    # No need to update here as _fetch_card_data already shows errors

        # Ensure the error message is displayed at the end
        if self.error_count > 0:
            print(f"\n{Colors.BOLD}{Colors.RED}Total cards not found: {self.error_count}{Colors.END}")
            if self.not_found_cards:
                # Show up to 10 cards not found at the end
                display_cards = self.not_found_cards[:10]
                cards_str = ", ".join([f"'{card}'" for card in display_cards])
                if len(self.not_found_cards) > 10:
                    cards_str += f" and {len(self.not_found_cards) - 10} more..."
                print(f"{Colors.YELLOW}Cards not found: {cards_str}{Colors.END}")

        # If there are no price changes, we're done
        if not changed_prices:
            logger.info("No price changes detected.")
            return
            
        logger.info(f"Found {len(changed_prices)} cards with price changes")
        
        # Reset the error counter for the update phase
        self.error_count = 0
        self.last_error_count = 0
        
        # Print an initial message for the update error counter
        print(f"{Colors.BOLD}Update error counter: {self.error_count}{Colors.END}")
        
        # Find the price column index only once
        price_col = self._get_price_column_index()
        
        # Update prices in larger batches to reduce API calls
        batch_size = 200  # Increased batch size
        batch_updates = []
        
        # Configure a new progress bar for price updates
        with tqdm(total=len(changed_prices), desc="Updating prices", unit="cards") as pbar:
            for row_index, card_name, new_price in changed_prices:
                cell = gspread.utils.rowcol_to_a1(row_index, price_col)
                batch_updates.append({
                    'range': cell,
                    'values': [[new_price]]
                })
                
                # Update in larger batches to reduce API calls
                if len(batch_updates) >= batch_size:
                    try:
                        self._batch_update_prices(batch_updates)
                    except Exception:
                        # If there's an error in the batch, increment the counter
                        self.error_count += len(batch_updates)
                    
                    pbar.update(len(batch_updates))
                    batch_updates = []
                    
                    # Update the error message below the progress bar
                    if self.error_count > 0 and self.error_count != self.last_error_count:
                        self._print_error_counter("update")
                    
                    # Add a small delay between batches to avoid hitting API limits
                    time.sleep(1.5)
                    
            # Update remaining items
            if batch_updates:
                try:
                    self._batch_update_prices(batch_updates)
                except Exception:
                    # If there's an error in the final batch, increment the counter
                    self.error_count += len(batch_updates)
                
                pbar.update(len(batch_updates))
                
                # Update the error message below the progress bar
                if self.error_count > 0 and self.error_count != self.last_error_count:
                    self._print_error_counter("update")
            
        # Ensure the error message is displayed at the end
        if self.error_count > 0:
            print(f"\n{Colors.BOLD}{Colors.RED}Total update errors: {self.error_count}{Colors.END}")
            
        logger.info(f"Price update completed in {datetime.now() - start_time}")
        
    def _get_price_column_index(self) -> int:
        """
        Get the column index for the Price column.
        
        Returns:
            Column index for the Price column (1-based)
        """
        try:
            # Try to get cached headers first to reduce API calls
            if hasattr(self, '_headers_cache'):
                headers = self._headers_cache
            else:
                headers = self.spreadsheet_client._worksheet.row_values(1)
                # Cache the headers
                self._headers_cache = headers
                
            # Column indices in gspread are 1-based
            return headers.index("Price") + 1
        except ValueError:
            logger.warning("Price column not found, using default index 13")
            return 13  # Default index for Price column (1-based)
        except Exception as e:
            logger.error(f"Error getting price column index: {e}")
            # Fallback to default index
            return 13
            
    def _batch_update_prices(self, batch_updates: List[Dict[str, Any]]) -> None:
        """
        Update prices in batches with exponential backoff retry.
        
        Args:
            batch_updates: List of batch update operations
        """
        max_retries = 5
        base_delay = 2  # Base delay in seconds
        
        for attempt in range(max_retries):
            try:
                self.spreadsheet_client._worksheet.batch_update(batch_updates)
                return
            except Exception as e:
                # Check if it's a quota exceeded error
                if 'Quota exceeded' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
                    # Calculate delay with exponential backoff and some randomness
                    delay = base_delay * (2 ** attempt) + (random.random() * 2)
                    if attempt < max_retries - 1:
                        logger.warning(f"API quota exceeded. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        logger.error(f"Failed to update prices after {max_retries} attempts: {e}")
                        raise
                else:
                    logger.error(f"Failed to batch update prices: {e}")
                    raise

    def _process_card_batch(self, cards: List[List[str]], start_idx: int) -> List[List[Any]]:
        """Process a batch of cards."""
        card_data = []
        
        for card in cards:
            data = self._fetch_card_data(card[0])
            
            if self.use_openai and data:
                data, game_strategy, tier = self.card_fetcher.get_card_info(data.get("name"))
            else:
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
                    self._process_price(data.get("prices", {}).get("eur")),
                    data.get("released_at"),
                    data.get("set"),
                    data.get("set_name"),
                    data.get("collector_number"),
                    data.get("edhrec_rank"),
                    game_strategy,
                    tier,
                ]
            else:
                cell_values = [card[0]] + ["N/A"] * 19
                
            card_data.append(cell_values)
            time.sleep(self.API_RATE_LIMIT_DELAY)
            
        return card_data

    def process_cards(self, cards: List[List[str]]) -> None:
        """Process cards with batching and parallel processing."""
        # Reset the error counter and the list of cards not found
        self.error_count = 0
        self.last_error_count = 0
        self.not_found_cards = []
        
        # Print an initial message for the error counter
        print(f"{Colors.BOLD}Cards not found counter: {self.error_count}{Colors.END}")
        
        row_index_to_start = self.spreadsheet_client.get_empty_row_index_to_start(2)
        cards = [card for i, card in enumerate(cards, start=1) if i >= row_index_to_start]
        
        # Configure tqdm to show only the progress bar with time estimation
        with tqdm(total=len(cards), desc="Processing cards", unit="cards") as pbar:
            for i in range(0, len(cards), self.BATCH_SIZE):
                batch = cards[i:i + self.BATCH_SIZE]
                card_data = self._process_card_batch(batch, i)
                
                if card_data:
                    range_start = gspread.utils.rowcol_to_a1(row_index_to_start + i, 1)
                    range_end = gspread.utils.rowcol_to_a1(
                        row_index_to_start + i + len(card_data),
                        len(card_data[0])
                    )
                    try:
                        self._update_sheet_with_retry(f"{range_start}:{range_end}", card_data)
                    except Exception:
                        # If there's an error updating, increment the counter
                        self.error_count += len(card_data)
                
                # Update the progress bar
                pbar.update(len(batch))
                
                # No need to update here as _fetch_card_data already shows errors
                
        # Ensure the error message is displayed at the end
        if self.error_count > 0:
            print(f"\n{Colors.BOLD}{Colors.RED}Total cards not found: {self.error_count}{Colors.END}")
            if self.not_found_cards:
                # Show up to 10 cards not found at the end
                display_cards = self.not_found_cards[:10]
                cards_str = ", ".join([f"'{card}'" for card in display_cards])
                if len(self.not_found_cards) > 10:
                    cards_str += f" and {len(self.not_found_cards) - 10} more..."
                print(f"{Colors.YELLOW}Cards not found: {cards_str}{Colors.END}")
            
        logger.info("Card processing completed successfully")

    def process_card_data(self) -> None:
        """Main processing method."""
        try:
            if self.update_prices:
                cards = self.spreadsheet_client.get_all_cards_prices()
                self.update_prices_data(cards)
            else:
                cards = self.spreadsheet_client.get_cards()
                self.process_cards(cards)
        except Exception as e:
            logger.error(f"Error processing card data: {e}")
            raise

    def _update_sheet_with_retry(self, column_or_range: str, data: List[Any]) -> None:
        """Update sheet with exponential backoff retry."""
        try:
            # Determine if we're updating a column or a range
            if ":" in column_or_range:
                # It's a cell range (e.g., "A1:B2")
                self.spreadsheet_client.update_cells(
                    column_or_range.split(":")[0],
                    column_or_range.split(":")[1],
                    data
                )
            else:
                # It's a column name
                self.spreadsheet_client.update_column(column_or_range, data)
            return
        except Exception as e:
            logger.error(f"Error updating sheet: {e}")
            raise Exception(f"Failed to update sheet: {e}")
