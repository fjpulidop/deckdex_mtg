import os
import time
import random
import csv
from typing import List, Dict, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from dotenv import load_dotenv
from .card_fetcher import CardFetcher
from .config import ProcessorConfig, ClientFactory
from .storage import get_collection_repository
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
    def __init__(self, config: ProcessorConfig):
        """Initialize MagicCardProcessor with configuration.
        
        Args:
            config: ProcessorConfig instance with all configuration parameters
        """
        self.config = config
        self.update_prices = config.update_prices
        self.dry_run = config.dry_run
        
        self._initialize_clients()
        self._card_cache = {}
        self.error_count = 0
        self.last_error_count = 0
        self.not_found_cards = []  # List to store names of cards not found

    def _initialize_clients(self) -> None:
        """Initialize card fetcher, optional collection repository (Postgres), and spreadsheet client (only when not using Postgres)."""
        self.card_fetcher = CardFetcher(
            scryfall_config=self.config.scryfall,
            openai_config=self.config.openai
        )
        url = getattr(self.config.database, "url", None) if self.config.database else None
        if not url:
            import os
            url = os.getenv("DATABASE_URL")
        self.collection_repository = get_collection_repository(url) if url else None
        # Only create spreadsheet client when not using Postgres (e.g. update_prices + repo never touches Sheets)
        self.spreadsheet_client = None
        if self.collection_repository is None:
            self.spreadsheet_client = ClientFactory.create_spreadsheet_client(self.config)

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
        Process a batch of cards for price updates (Sheet path: row_index, name, new_price).
        """
        updated_data = []
        for i, card in enumerate(cards[start_idx:start_idx + batch_size], start=start_idx):
            card_name, current_price = card
            data = self._fetch_card_data(card_name)
            new_price_raw = data.get("prices", {}).get("eur") if data else None
            new_price = self._process_price(new_price_raw)
            if new_price != current_price:
                row_index = i + 2
                updated_data.append((row_index, card_name, new_price))
            time.sleep(self.config.processing.api_delay)
        return updated_data

    def _update_prices_batch_repo(
        self, cards: List[Tuple[int, str, str]], start_idx: int, batch_size: int
    ) -> List[Tuple[int, str, str]]:
        """
        Process a batch of cards for price updates (Repo path: card_id, name, new_price).
        cards: list of (card_id, card_name, current_price_str).
        Returns: list of (card_id, card_name, new_price) for changed prices.
        """
        updated_data = []
        for i, (card_id, card_name, current_price) in enumerate(
            cards[start_idx : start_idx + batch_size], start=start_idx
        ):
            data = self._fetch_card_data(card_name)
            new_price_raw = data.get("prices", {}).get("eur") if data else None
            new_price = self._process_price(new_price_raw)
            if new_price != current_price:
                updated_data.append((card_id, card_name, new_price))
            time.sleep(self.config.processing.api_delay)
        return updated_data

    def _print_error_counter(self, phase: str = "search") -> None:
        """
        Print the error counter with single-line refresh formatting.
        
        Args:
            phase: Phase of the process (search or update)
        """
        if self.error_count > 0:
            # Use carriage return to update the same line
            error_msg = f"\r{Colors.BOLD}{Colors.RED}Cards not found: {self.error_count}{Colors.END}"
            print(error_msg, end='', flush=True)
    
    def _save_failed_cards_csv(self) -> Optional[str]:
        """
        Save failed cards to a CSV file in the output/ directory.
        
        Returns:
            Path to the CSV file if any cards failed, None otherwise
        """
        if not self.not_found_cards:
            return None
        
        # Create output directory if it doesn't exist
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = os.path.join(output_dir, f"failed_cards_{timestamp}.csv")
        
        # Write CSV with failed cards
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow(['card_name', 'error_type', 'timestamp'])
                
                # Write each failed card
                for card_name in self.not_found_cards:
                    writer.writerow([
                        card_name,
                        'not_found',
                        datetime.now().isoformat()
                    ])
            
            logger.info(f"Failed cards saved to {csv_path}")
            return csv_path
        except Exception as e:
            logger.error(f"Failed to save error CSV: {e}")
            return None

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
        pending_changes = []  # Buffer for price changes
        batches_processed = 0  # Counter for batches since last write
        write_counter = 0  # Counter for write notifications
        total_cards = len(cards)
        total_prices_updated = 0  # Track total updates for final summary
        
        # Print an initial message for the error counter (will be updated in place)
        print(f"{Colors.BOLD}Cards not found: 0{Colors.END}", end='', flush=True)
        
        # Configure tqdm to show only the progress bar with time estimation
        with tqdm(total=total_cards, desc="Verifying prices", unit="cards") as pbar:
            with ThreadPoolExecutor(max_workers=self.config.processing.max_workers) as executor:
                futures = []
                for i in range(0, len(cards), self.config.processing.batch_size):
                    futures.append(
                        executor.submit(self._update_prices_batch, cards, i, self.config.processing.batch_size)
                    )
                
                for future in futures:
                    batch_results = future.result()
                    pending_changes.extend(batch_results)
                    batches_processed += 1
                    
                    # Update the progress bar with the processed batch size
                    pbar.update(min(self.config.processing.batch_size, total_cards - pbar.n))
                    
                    # Check if we should write the buffered changes
                    if batches_processed >= self.config.processing.write_buffer_batches:
                        if pending_changes:
                            write_counter += 1
                            cards_in_buffer = batches_processed * self.config.processing.batch_size
                            num_written = self._write_buffered_prices(pending_changes)
                            
                            # Print progress notification
                            if num_written > 0:
                                print(f"\n{Colors.GREEN}✓ Write #{write_counter} ({cards_in_buffer} cards): {num_written} updates{Colors.END}")
                            
                            total_prices_updated += num_written
                            
                            # Reset buffer and counter
                            pending_changes = []
                            batches_processed = 0
                            
                            # Rate limiting delay
                            time.sleep(1.5)

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
            
            # Save failed cards to CSV
            csv_path = self._save_failed_cards_csv()
            if csv_path:
                print(f"{Colors.CYAN}📄 Failed cards saved to: {csv_path}{Colors.END}")

        # Write remaining pending changes (partial buffer)
        if pending_changes:
            write_counter += 1
            cards_in_buffer = batches_processed * self.config.processing.batch_size
            num_written = self._write_buffered_prices(pending_changes)
            
            if num_written > 0:
                print(f"\n{Colors.GREEN}✓ Write #{write_counter} ({cards_in_buffer} cards): {num_written} updates{Colors.END}")
            
            total_prices_updated += num_written
        
        # Final summary
        if total_prices_updated == 0:
            logger.info("No price changes detected.")
        else:
            print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Completed: {total_cards} cards verified, {total_prices_updated} prices updated{Colors.END}")
            print(f"{Colors.CYAN}💡 To resume from here: --resume-from {total_cards + 2}{Colors.END}")
            
        logger.info(f"Price update completed in {datetime.now() - start_time}")

    def update_prices_data_repo(self, cards: List[Tuple[int, str, str]]) -> None:
        """
        Update prices using the collection repository (Postgres). cards: list of (card_id, name, current_price_str).
        """
        if not self.collection_repository:
            raise RuntimeError("collection_repository not set")
        logger.info("Checking price updates from Scryfall API (Postgres)...")
        start_time = datetime.now()
        self.error_count = 0
        self.last_error_count = 0
        self.not_found_cards = []
        total_cards = len(cards)
        total_prices_updated = 0
        print(f"{Colors.BOLD}Cards not found: 0{Colors.END}", end="", flush=True)
        with tqdm(total=total_cards, desc="Verifying prices", unit="cards") as pbar:
            with ThreadPoolExecutor(max_workers=self.config.processing.max_workers) as executor:
                futures = []
                for i in range(0, len(cards), self.config.processing.batch_size):
                    futures.append(
                        executor.submit(
                            self._update_prices_batch_repo,
                            cards,
                            i,
                            self.config.processing.batch_size,
                        )
                    )
                for future in futures:
                    batch_results = future.result()
                    for card_id, _name, new_price in batch_results:
                        self.collection_repository.update(card_id, {"price_eur": new_price})
                        total_prices_updated += 1
                    pbar.update(min(self.config.processing.batch_size, total_cards - pbar.n))
        if self.error_count > 0:
            print(f"\n{Colors.BOLD}{Colors.RED}Total cards not found: {self.error_count}{Colors.END}")
        if total_prices_updated > 0:
            print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Completed: {total_cards} cards verified, {total_prices_updated} prices updated{Colors.END}")
        logger.info(f"Price update (Postgres) completed in {datetime.now() - start_time}")

    def process_cards_repo(self) -> None:
        """
        Full card processing against Postgres: read cards (all or only new/incomplete),
        fetch fresh data from Scryfall (and optional OpenAI), update each card in the repository.
        """
        if not self.collection_repository:
            raise RuntimeError("collection_repository not set")
        only_incomplete = getattr(self.config, "process_scope", None) == "new_only"
        if only_incomplete:
            cards = self.collection_repository.get_cards_for_process(only_incomplete=True)
            logger.info(f"Processing only new/incomplete cards (with only name): {len(cards)} cards")
        else:
            all_cards = self.collection_repository.get_all_cards()
            cards = [c for c in all_cards if c.get("id") is not None]
        if self.config.limit is not None:
            cards = cards[: self.config.limit]
            logger.info(f"Limiting processing to {self.config.limit} cards")
        if self.config.resume_from is not None:
            cards = cards[self.config.resume_from :]
            logger.info(f"Resuming from index {self.config.resume_from}")
        self.error_count = 0
        self.last_error_count = 0
        self.not_found_cards = []
        print(f"{Colors.BOLD}Cards not found counter: {self.error_count}{Colors.END}")
        total = len(cards)
        with tqdm(total=total, desc="Processing cards", unit="cards") as pbar:
            for i in range(0, len(cards), self.config.processing.batch_size):
                batch = cards[i : i + self.config.processing.batch_size]
                for card in batch:
                    card_id = card.get("id")
                    name = card.get("name") or card.get("english_name")
                    if not name or card_id is None:
                        pbar.update(1)
                        continue
                    data = self._fetch_card_data(name)
                    if self.config.openai.enabled and data:
                        data, game_strategy, tier = self.card_fetcher.get_card_info(data.get("name"))
                    else:
                        game_strategy, tier = None, None
                    if data:
                        price_eur = self._process_price(data.get("prices", {}).get("eur"))
                        cmc_val = data.get("cmc")
                        if cmc_val is not None and str(cmc_val).strip() in ("", "N/A"):
                            cmc_val = None
                        elif cmc_val is not None:
                            try:
                                cmc_val = float(cmc_val)
                            except (TypeError, ValueError):
                                cmc_val = None
                        update = {
                            "type_line": data.get("type_line"),
                            "description": data.get("oracle_text"),
                            "keywords": str(data.get("keywords")) if data.get("keywords") is not None else None,
                            "mana_cost": data.get("mana_cost"),
                            "cmc": cmc_val,
                            "colors": str(data.get("colors")) if data.get("colors") is not None else None,
                            "color_identity": str(data.get("color_identity")) if data.get("color_identity") is not None else None,
                            "power": data.get("power"),
                            "toughness": data.get("toughness"),
                            "rarity": data.get("rarity"),
                            "price_eur": price_eur,
                            "release_date": data.get("released_at"),
                            "set_id": data.get("set"),
                            "set_name": data.get("set_name"),
                            "set_number": data.get("collector_number"),
                            "edhrec_rank": str(data.get("edhrec_rank")) if data.get("edhrec_rank") is not None else None,
                            "game_strategy": game_strategy,
                            "tier": tier,
                        }
                        update = {k: v for k, v in update.items() if v is not None}
                        if update:
                            self.collection_repository.update(card_id, update)
                    time.sleep(self.config.processing.api_delay)
                    pbar.update(1)
        if self.error_count > 0:
            print(f"\n{Colors.BOLD}{Colors.RED}Total cards not found: {self.error_count}{Colors.END}")
            if self.not_found_cards:
                display_cards = self.not_found_cards[:10]
                cards_str = ", ".join(f"'{c}'" for c in display_cards)
                if len(self.not_found_cards) > 10:
                    cards_str += f" and {len(self.not_found_cards) - 10} more..."
                print(f"{Colors.YELLOW}Cards not found: {cards_str}{Colors.END}")
        logger.info("Card processing (Postgres) completed successfully")

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
    
    def _convert_price_to_numeric(self, price_str: str) -> Any:
        """
        Convert price string to numeric value for Google Sheets.
        
        Args:
            price_str: Price string (e.g., "1,50", "2.30", "N/A")
            
        Returns:
            Float value if valid number, "N/A" if invalid or missing
        """
        if not price_str or price_str == "N/A":
            return "N/A"
        
        try:
            # Replace comma with period for European decimal format
            normalized = price_str.replace(",", ".")
            return float(normalized)
        except (ValueError, AttributeError):
            logger.warning(f"Could not convert price '{price_str}' to numeric, using 'N/A'")
            return "N/A"
    
    def _write_buffered_prices(self, changes: List[Tuple[int, str, str]]) -> int:
        """Write buffered price changes to Google Sheets as numeric values.
        
        Args:
            changes: List of (row_index, card_name, new_price) tuples
            
        Returns:
            Number of prices actually written
        """
        if not changes:
            return 0
            
        try:
            # Get the price column index (cached)
            price_col = self._get_price_column_index()
            
            # Construct batch update operations with numeric values
            batch_updates = []
            for row_index, card_name, new_price in changes:
                cell = gspread.utils.rowcol_to_a1(row_index, price_col)
                # Convert price to numeric value
                numeric_price = self._convert_price_to_numeric(new_price)
                batch_updates.append({
                    'range': cell,
                    'values': [[numeric_price]]
                })
            
            # Write to Google Sheets using existing retry logic
            self._batch_update_prices(batch_updates)
            
            return len(changes)
            
        except Exception as e:
            # Log error and continue (maintain existing error strategy)
            logger.error(f"Failed to write buffered prices: {e}")
            self.error_count += len(changes)
            return 0
            
    def _batch_update_prices(self, batch_updates: List[Dict[str, Any]]) -> None:
        """
        Update prices in batches with exponential backoff retry.
        
        Args:
            batch_updates: List of batch update operations
        """
        max_retries = self.config.google_sheets.max_retries
        base_delay = self.config.google_sheets.retry_delay
        
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
            
            if self.config.openai.enabled and data:
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
            time.sleep(self.config.processing.api_delay)
            
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
        
        # Apply limit if configured
        if self.config.limit is not None:
            cards = cards[:self.config.limit]
            logger.info(f"Limiting processing to {self.config.limit} cards")
        
        # Apply resume_from if configured
        if self.config.resume_from is not None:
            cards = cards[self.config.resume_from - row_index_to_start:]
            logger.info(f"Resuming from row {self.config.resume_from}")
        
        # Configure tqdm to show only the progress bar with time estimation
        with tqdm(total=len(cards), desc="Processing cards", unit="cards") as pbar:
            for i in range(0, len(cards), self.config.processing.batch_size):
                batch = cards[i:i + self.config.processing.batch_size]
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
        """Main processing method. Uses collection repository (Postgres) when configured; else Spreadsheet."""
        try:
            if self.update_prices:
                if self.collection_repository:
                    cards = self.collection_repository.get_cards_for_price_update()
                    self.update_prices_data_repo(cards)
                else:
                    cards = self.spreadsheet_client.get_all_cards_prices()
                    self.update_prices_data(cards)
            else:
                if self.collection_repository:
                    self.process_cards_repo()
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
