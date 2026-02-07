from typing import List, Any, Optional, Dict
import gspread
from gspread.exceptions import APIError
from loguru import logger
from google.oauth2.service_account import Credentials


class SpreadsheetClient:
    """Client for interacting with Google Sheets."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self, credentials_path: str, spreadsheet_name: str, worksheet_name: str):
        """
        Initialize the SpreadsheetClient.
        
        Args:
            credentials_path: Path to the Google API credentials file.
            spreadsheet_name: Name of the target spreadsheet.
            worksheet_name: Name of the target worksheet.
        """
        self.credentials_path = credentials_path
        self.spreadsheet_name = spreadsheet_name
        self.worksheet_name = worksheet_name
        self._client = None
        self._worksheet = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Google Sheets."""
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            self._client = gspread.authorize(credentials)
            spreadsheet = self._client.open(self.spreadsheet_name)
            self._worksheet = spreadsheet.worksheet(self.worksheet_name)
            logger.info(f"Connected to spreadsheet '{self.spreadsheet_name}', worksheet '{self.worksheet_name}'")
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            raise

    def _ensure_connection(self) -> None:
        """Ensure connection is active, reconnect if necessary with exponential backoff."""
        max_retries = 5
        base_delay = 2  # Base delay in seconds
        
        for attempt in range(max_retries):
            try:
                if not self._worksheet:
                    self._connect()
                # Test connection with a lightweight operation
                self._worksheet.row_count
                return
            except Exception as e:
                error_str = str(e)
                if 'Quota exceeded' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                    # Calculate delay with exponential backoff and some randomness
                    import random
                    delay = base_delay * (2 ** attempt) + (random.random() * 2)
                    if attempt < max_retries - 1:
                        logger.warning(f"API quota exceeded. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})")
                        import time
                        time.sleep(delay)
                    else:
                        logger.error(f"Failed to connect after {max_retries} attempts due to quota limits: {e}")
                        raise
                else:
                    # For other errors, try to reconnect once
                    logger.warning(f"Connection error: {e}. Attempting to reconnect...")
                    try:
                        self._connect()
                        return
                    except Exception as reconnect_error:
                        logger.error(f"Failed to reconnect: {reconnect_error}")
                        raise

    def get_empty_row_index_to_start(self, column_index: int = 1) -> int:
        """
        Find the first empty row in the specified column.
        
        Args:
            column_index: Index of the column to check (1-based).
            
        Returns:
            Index of the first empty row (1-based).
        """
        self._ensure_connection()
        try:
            column_values = self._worksheet.col_values(column_index)
            return len(column_values) + 1
        except APIError as e:
            logger.error(f"Failed to get empty row index: {e}")
            raise

    def get_cards(self) -> List[List[str]]:
        """
        Get all cards from the worksheet.
        
        Returns:
            List of card rows, where each row is a list of values.
        """
        self._ensure_connection()
        try:
            return self._worksheet.get_all_values()
        except APIError as e:
            logger.error(f"Failed to get cards: {e}")
            raise

    def get_all_cards_prices(self) -> List[List[str]]:
        """
        Get all card names and their current prices.
        Uses "English name" column for lookup, with fallback to "Name" if empty.
        
        Returns:
            List of [card_name, current_price] entries.
        """
        self._ensure_connection()
        try:
            # Get all values from the worksheet
            all_values = self._worksheet.get_all_values()
            
            # Skip header row
            data_rows = all_values[1:]
            
            # Find column indices
            headers = all_values[0]
            
            # Find Price column
            try:
                price_col_idx = headers.index("Price")
            except ValueError:
                logger.warning("Price column not found, using default index 12")
                price_col_idx = 12  # Default index for Price column (0-based)
            
            # Find English name column (preferred) and Name column (fallback)
            try:
                english_name_col_idx = headers.index("English name")
            except ValueError:
                logger.warning("English name column not found, will use Name column only")
                english_name_col_idx = None
            
            try:
                name_col_idx = headers.index("Name")
            except ValueError:
                logger.warning("Name column not found, using default index 0")
                name_col_idx = 0  # Default to first column
            
            # Return card names and their current prices
            # Use English name if available and not empty, otherwise fallback to Name
            result = []
            for row in data_rows:
                if not row:
                    continue
                
                # Determine which name to use
                card_name = None
                if english_name_col_idx is not None and english_name_col_idx < len(row):
                    card_name = row[english_name_col_idx].strip()
                
                # Fallback to Name column if English name is empty
                if not card_name and name_col_idx < len(row):
                    card_name = row[name_col_idx].strip()
                
                if card_name:
                    price = row[price_col_idx] if price_col_idx < len(row) else "N/A"
                    result.append([card_name, price])
            
            return result
            
        except APIError as e:
            logger.error(f"Failed to get card prices: {e}")
            raise

    def update_column(self, column_name: str, values: List[str]) -> None:
        """
        Update an entire column with new values.
        
        Args:
            column_name: Name of the column to update.
            values: New values to set in the column.
        """
        self._ensure_connection()
        try:
            # Find column index
            headers = self._worksheet.row_values(1)
            try:
                col_idx = headers.index(column_name) + 1
            except ValueError:
                raise ValueError(f"Column '{column_name}' not found in worksheet")

            # Update column in batches to avoid rate limits
            BATCH_SIZE = 500  # Increased batch size
            for i in range(0, len(values), BATCH_SIZE):
                batch = values[i:i + BATCH_SIZE]
                cells = []
                for row_idx, value in enumerate(batch, start=2 + i):
                    cells.append({
                        'range': f'{gspread.utils.rowcol_to_a1(row_idx, col_idx)}',
                        'values': [[value]]
                    })
                
                # Use exponential backoff for batch updates
                self._batch_update_with_retry(cells)
                
                # Add a delay between batches to avoid hitting rate limits
                if i + BATCH_SIZE < len(values):
                    import time
                    time.sleep(2)  # 2 second delay between batches
                
                logger.debug(f"Updated {len(batch)} values in column '{column_name}' (batch {i//BATCH_SIZE + 1}/{(len(values) + BATCH_SIZE - 1)//BATCH_SIZE})")

        except Exception as e:
            logger.error(f"Failed to update column '{column_name}': {e}")
            raise
            
    def _batch_update_with_retry(self, cells: List[Dict[str, Any]]) -> None:
        """
        Update cells in batches with exponential backoff retry.
        
        Args:
            cells: List of cell update operations
        """
        import time
        import random
        
        max_retries = 5
        base_delay = 2  # Base delay in seconds
        
        for attempt in range(max_retries):
            try:
                self._worksheet.batch_update(cells)
                return
            except Exception as e:
                error_str = str(e)
                if 'Quota exceeded' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                    # Calculate delay with exponential backoff and some randomness
                    delay = base_delay * (2 ** attempt) + (random.random() * 2)
                    if attempt < max_retries - 1:
                        logger.warning(f"API quota exceeded. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        logger.error(f"Failed to update after {max_retries} attempts due to quota limits: {e}")
                        raise
                else:
                    logger.error(f"Failed to batch update: {e}")
                    raise

    def update_cells(self, range_start: str, range_end: str, values: List[List[Any]]) -> None:
        """
        Update a range of cells with new values.
        
        Args:
            range_start: Start of the range (A1 notation).
            range_end: End of the range (A1 notation).
            values: New values to set in the range.
        """
        self._ensure_connection()
        try:
            cell_range = f"{range_start}:{range_end}"
            
            # For large updates, split into smaller batches
            if len(values) > 100:
                logger.info(f"Large update detected ({len(values)} rows). Splitting into batches.")
                BATCH_SIZE = 50
                for i in range(0, len(values), BATCH_SIZE):
                    batch = values[i:i + BATCH_SIZE]
                    # Calculate the batch range
                    start_row = int(''.join(filter(str.isdigit, range_start))) + i
                    end_row = min(start_row + len(batch) - 1, int(''.join(filter(str.isdigit, range_end))))
                    start_col = ''.join(filter(str.isalpha, range_start))
                    end_col = ''.join(filter(str.isalpha, range_end))
                    batch_range = f"{start_col}{start_row}:{end_col}{end_row}"
                    
                    # Update with retry
                    self._update_range_with_retry(batch_range, batch)
                    
                    # Add a delay between batches
                    if i + BATCH_SIZE < len(values):
                        import time
                        time.sleep(2)  # 2 second delay between batches
                    
                    logger.debug(f"Updated batch {i//BATCH_SIZE + 1}/{(len(values) + BATCH_SIZE - 1)//BATCH_SIZE} in range {batch_range}")
            else:
                # For smaller updates, update all at once
                self._update_range_with_retry(cell_range, values)
                logger.debug(f"Updated range {cell_range}")
                
        except APIError as e:
            logger.error(f"Failed to update cells in range {range_start}:{range_end}: {e}")
            raise
            
    def _update_range_with_retry(self, cell_range: str, values: List[List[Any]]) -> None:
        """
        Update a range of cells with exponential backoff retry.
        
        Args:
            cell_range: Range to update in A1 notation
            values: Values to set in the range
        """
        import time
        import random
        
        max_retries = 5
        base_delay = 2  # Base delay in seconds
        
        for attempt in range(max_retries):
            try:
                self._worksheet.update(cell_range, values)
                return
            except Exception as e:
                error_str = str(e)
                if 'Quota exceeded' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                    # Calculate delay with exponential backoff and some randomness
                    delay = base_delay * (2 ** attempt) + (random.random() * 2)
                    if attempt < max_retries - 1:
                        logger.warning(f"API quota exceeded. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        logger.error(f"Failed to update range after {max_retries} attempts due to quota limits: {e}")
                        raise
                else:
                    logger.error(f"Failed to update range: {e}")
                    raise
