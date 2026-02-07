"""Dry-run client for simulating Google Sheets operations without writing."""

from typing import List, Any
from loguru import logger


class DryRunClient:
    """Mock client that simulates SpreadsheetClient operations without executing them.
    
    This client implements the same interface as SpreadsheetClient but logs operations
    instead of performing actual writes to Google Sheets. It's used for testing and
    dry-run mode to validate changes before applying them.
    """
    
    def __init__(self, config):
        """Initialize DryRunClient.
        
        Args:
            config: ProcessorConfig instance
        """
        self.config = config
        self.sheet_name = config.sheet_name
        self.worksheet_name = config.worksheet_name
        
        # Statistics tracking
        self.stats = {
            "get_cards_calls": 0,
            "get_all_cards_prices_calls": 0,
            "update_column_calls": 0,
            "update_cells_calls": 0,
            "batch_update_calls": 0,
            "total_rows_would_update": 0,
        }
        
        # Sample data for display
        self.sample_updates = []
        
        logger.info(f"DRY RUN: Initialized for spreadsheet '{self.sheet_name}', worksheet '{self.worksheet_name}'")
    
    def get_cards(self) -> List[List[str]]:
        """Mock getting all cards from the worksheet.
        
        Returns:
            Empty list (dry-run doesn't need real data for most operations)
        """
        self.stats["get_cards_calls"] += 1
        logger.debug("DRY RUN: Would call get_cards()")
        # Return empty to avoid processing in dry-run
        # In a real dry-run we might want to fetch real data, but for safety we don't
        return []
    
    def get_all_cards_prices(self) -> List[List[str]]:
        """Mock getting all card names and prices.
        Uses "English name" column for lookup, with fallback to "Name" if empty.
        
        Returns:
            Empty list (dry-run doesn't need real data)
        """
        self.stats["get_all_cards_prices_calls"] += 1
        logger.debug("DRY RUN: Would call get_all_cards_prices() using 'English name' column (fallback to 'Name')")
        return []
    
    def get_empty_row_index_to_start(self, column_index: int = 1) -> int:
        """Mock finding the first empty row.
        
        Args:
            column_index: Column to check (1-based)
            
        Returns:
            2 (simulated: header in row 1, data starts at row 2)
        """
        logger.debug(f"DRY RUN: Would call get_empty_row_index_to_start({column_index})")
        return 2
    
    def update_column(self, column_name: str, values: List[str]) -> None:
        """Mock updating an entire column.
        
        Args:
            column_name: Name of the column to update
            values: New values for the column
        """
        self.stats["update_column_calls"] += 1
        self.stats["total_rows_would_update"] += len(values)
        
        logger.info(f"DRY RUN: Would update column '{column_name}' with {len(values)} values")
        
        # Store sample for display
        sample_size = min(3, len(values))
        if sample_size > 0:
            self.sample_updates.append({
                "type": "column",
                "column": column_name,
                "rows": len(values),
                "sample": values[:sample_size]
            })
    
    def update_cells(self, range_start: str, range_end: str, values: List[List[Any]]) -> None:
        """Mock updating a range of cells.
        
        Args:
            range_start: Start of the range (A1 notation)
            range_end: End of the range (A1 notation)
            values: New values for the range
        """
        self.stats["update_cells_calls"] += 1
        self.stats["total_rows_would_update"] += len(values)
        
        logger.info(f"DRY RUN: Would update range {range_start}:{range_end} with {len(values)} rows")
        
        # Store sample for display
        sample_size = min(3, len(values))
        if sample_size > 0:
            self.sample_updates.append({
                "type": "range",
                "range": f"{range_start}:{range_end}",
                "rows": len(values),
                "sample": values[:sample_size]
            })
    
    def _batch_update_with_retry(self, cells: List[Any]) -> None:
        """Mock batch update with retry logic.
        
        Args:
            cells: List of cell update operations
        """
        self.stats["batch_update_calls"] += 1
        logger.debug(f"DRY RUN: Would batch update {len(cells)} cells")
    
    def get_stats(self) -> dict:
        """Get statistics about operations that would be performed.
        
        Returns:
            Dictionary with operation counts and samples
        """
        return {
            **self.stats,
            "sample_updates": self.sample_updates
        }
    
    def display_summary(self):
        """Display a summary of operations that would be performed."""
        logger.info("\n" + "="*60)
        logger.info("DRY RUN SUMMARY")
        logger.info("="*60)
        logger.info(f"Spreadsheet: {self.sheet_name}")
        logger.info(f"Worksheet: {self.worksheet_name}")
        logger.info(f"Total rows that would be updated: {self.stats['total_rows_would_update']}")
        logger.info(f"Update operations:")
        logger.info(f"  - Column updates: {self.stats['update_column_calls']}")
        logger.info(f"  - Range updates: {self.stats['update_cells_calls']}")
        logger.info(f"  - Batch updates: {self.stats['batch_update_calls']}")
        
        if self.sample_updates:
            logger.info("\nSample updates (first 3 per operation):")
            for i, update in enumerate(self.sample_updates[:3], 1):
                if update["type"] == "column":
                    logger.info(f"\n{i}. Column '{update['column']}' ({update['rows']} rows):")
                    for j, val in enumerate(update["sample"], 1):
                        logger.info(f"   Row {j}: {val}")
                elif update["type"] == "range":
                    logger.info(f"\n{i}. Range {update['range']} ({update['rows']} rows):")
                    for j, row in enumerate(update["sample"], 1):
                        logger.info(f"   Row {j}: {row[:5]}...")  # Show first 5 columns
        
        logger.info("\n" + "="*60)
        logger.info("To execute for real, run without --dry-run")
        logger.info("="*60 + "\n")
