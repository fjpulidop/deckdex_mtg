#!/usr/bin/env python
"""Test suite for DeckDex MTG main CLI and configuration."""

import unittest
from unittest.mock import patch, MagicMock, Mock
from deckdex.config import ProcessorConfig, ClientFactory
from deckdex.magic_card_processor import MagicCardProcessor
from deckdex.dry_run_client import DryRunClient


class TestProcessorConfig(unittest.TestCase):
    """Test suite for ProcessorConfig dataclass."""
    
    def test_config_creation_with_defaults(self):
        """Test ProcessorConfig creation with default values."""
        config = ProcessorConfig()
        
        # Behavioral flags
        self.assertFalse(config.use_openai)
        self.assertFalse(config.update_prices)
        self.assertFalse(config.dry_run)
        self.assertFalse(config.verbose)
        
        # Performance settings
        self.assertEqual(config.batch_size, 20)
        self.assertEqual(config.max_workers, 4)
        self.assertEqual(config.api_delay, 0.1)
        self.assertEqual(config.max_retries, 5)
        
        # Google Sheets settings
        self.assertIsNone(config.credentials_path)
        self.assertEqual(config.sheet_name, "magic")
        self.assertEqual(config.worksheet_name, "cards")
        
        # Processing control
        self.assertIsNone(config.limit)
        self.assertIsNone(config.resume_from)
    
    def test_config_creation_with_custom_values(self):
        """Test ProcessorConfig creation with custom values."""
        config = ProcessorConfig(
            use_openai=True,
            batch_size=50,
            max_workers=8,
            api_delay=0.2,
            limit=100,
            resume_from=50
        )
        
        self.assertTrue(config.use_openai)
        self.assertEqual(config.batch_size, 50)
        self.assertEqual(config.max_workers, 8)
        self.assertEqual(config.api_delay, 0.2)
        self.assertEqual(config.limit, 100)
        self.assertEqual(config.resume_from, 50)
    
    def test_config_validation_invalid_batch_size(self):
        """Test ProcessorConfig validation for invalid batch_size."""
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(batch_size=0)
        self.assertIn("batch_size must be > 0", str(cm.exception))
        
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(batch_size=-5)
        self.assertIn("batch_size must be > 0", str(cm.exception))
    
    def test_config_validation_invalid_max_workers(self):
        """Test ProcessorConfig validation for invalid max_workers."""
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(max_workers=0)
        self.assertIn("max_workers must be between 1 and 10", str(cm.exception))
        
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(max_workers=15)
        self.assertIn("max_workers must be between 1 and 10", str(cm.exception))
    
    def test_config_validation_invalid_api_delay(self):
        """Test ProcessorConfig validation for invalid api_delay."""
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(api_delay=-0.1)
        self.assertIn("api_delay must be >= 0", str(cm.exception))
    
    def test_config_validation_invalid_max_retries(self):
        """Test ProcessorConfig validation for invalid max_retries."""
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(max_retries=0)
        self.assertIn("max_retries must be >= 1", str(cm.exception))
    
    def test_config_validation_invalid_limit(self):
        """Test ProcessorConfig validation for invalid limit."""
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(limit=0)
        self.assertIn("limit must be > 0", str(cm.exception))
        
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(limit=-5)
        self.assertIn("limit must be > 0", str(cm.exception))
    
    def test_config_validation_invalid_resume_from(self):
        """Test ProcessorConfig validation for invalid resume_from."""
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(resume_from=0)
        self.assertIn("resume_from must be >= 1", str(cm.exception))
        
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(resume_from=-5)
        self.assertIn("resume_from must be >= 1", str(cm.exception))


class TestClientFactory(unittest.TestCase):
    """Test suite for ClientFactory."""
    
    @patch("deckdex.spreadsheet_client.SpreadsheetClient")
    @patch.dict("os.environ", {"GOOGLE_API_CREDENTIALS": "/path/to/creds.json"})  
    def test_factory_returns_spreadsheet_client_when_dry_run_false(self, mock_spreadsheet_class):
        """Test ClientFactory returns SpreadsheetClient when dry_run=False."""
        config = ProcessorConfig(dry_run=False)
        
        client = ClientFactory.create_spreadsheet_client(config)
        
        # Verify SpreadsheetClient was instantiated with correct parameters
        mock_spreadsheet_class.assert_called_once_with(
            "/path/to/creds.json",
            "magic",
            "cards"
        )
    
    def test_factory_returns_dry_run_client_when_dry_run_true(self):
        """Test ClientFactory returns DryRunClient when dry_run=True."""
        config = ProcessorConfig(dry_run=True)
        
        client = ClientFactory.create_spreadsheet_client(config)
        
        self.assertIsInstance(client, DryRunClient)


class TestDryRunClient(unittest.TestCase):
    """Test suite for DryRunClient."""
    
    def test_dry_run_client_logs_operations_without_executing(self):
        """Test DryRunClient logs operations without executing writes."""
        config = ProcessorConfig(dry_run=True)
        client = DryRunClient(config)
        
        # Test update_column
        client.update_column("Price", ["1.00", "2.00", "3.00"])
        self.assertEqual(client.stats["update_column_calls"], 1)
        self.assertEqual(client.stats["total_rows_would_update"], 3)
        
        # Test update_cells
        client.update_cells("A2", "B4", [["row1"], ["row2"], ["row3"]])
        self.assertEqual(client.stats["update_cells_calls"], 1)
        self.assertEqual(client.stats["total_rows_would_update"], 6)  # 3 + 3
        
        # Verify operations were logged, not executed
        self.assertGreater(len(client.sample_updates), 0)


class TestMagicCardProcessor(unittest.TestCase):
    """Test suite for MagicCardProcessor with ProcessorConfig."""
    
    @patch("deckdex.config.ClientFactory.create_spreadsheet_client")
    @patch("deckdex.magic_card_processor.CardFetcher")
    def test_processor_uses_config_values(self, mock_card_fetcher_class, mock_client_factory):
        """Test MagicCardProcessor uses configuration values."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_factory.return_value = mock_client
        mock_card_fetcher = MagicMock()
        mock_card_fetcher_class.return_value = mock_card_fetcher
        
        # Create config with custom values
        config = ProcessorConfig(
            batch_size=50,
            max_workers=8,
            api_delay=0.2,
            max_retries=10
        )
        
        # Create processor
        processor = MagicCardProcessor(config)
        
        # Verify config values are used
        self.assertEqual(processor.batch_size, 50)
        self.assertEqual(processor.max_workers, 8)
        self.assertEqual(processor.api_delay, 0.2)
        self.assertEqual(processor.max_retries, 10)
        
        # Verify CardFetcher was initialized with config values
        mock_card_fetcher_class.assert_called_once_with(
            max_retries=10,
            retry_delay=0.2
        )


class TestBackwardsCompatibility(unittest.TestCase):
    """Test suite for backwards compatibility."""
    
    @patch("deckdex.config.ClientFactory.create_spreadsheet_client")
    @patch("deckdex.magic_card_processor.CardFetcher")
    def test_default_config_matches_old_behavior(self, mock_card_fetcher_class, mock_client_factory):
        """Test default config values match old hardcoded constants."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_factory.return_value = mock_client
        mock_card_fetcher = MagicMock()
        mock_card_fetcher_class.return_value = mock_card_fetcher
        
        # Create processor with default config
        config = ProcessorConfig()
        processor = MagicCardProcessor(config)
        
        # Verify defaults match old constants
        self.assertEqual(processor.batch_size, 20)  # Old BATCH_SIZE
        self.assertEqual(processor.max_workers, 4)  # Old hardcoded value
        self.assertEqual(processor.max_retries, 5)  # Old MAX_RETRIES
        # Note: api_delay changed from 0.05 to 0.1 (intentional improvement)
    
    @patch("deckdex.config.ClientFactory.create_spreadsheet_client")
    @patch("deckdex.magic_card_processor.CardFetcher")
    def test_use_openai_flag_still_works(self, mock_card_fetcher_class, mock_client_factory):
        """Test use_openai flag still works as before."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_factory.return_value = mock_client
        mock_card_fetcher = MagicMock()
        mock_card_fetcher_class.return_value = mock_card_fetcher
        
        # Create config with use_openai=True
        config = ProcessorConfig(use_openai=True)
        processor = MagicCardProcessor(config)
        
        self.assertTrue(processor.use_openai)
    
    @patch("deckdex.config.ClientFactory.create_spreadsheet_client")
    @patch("deckdex.magic_card_processor.CardFetcher")
    def test_update_prices_flag_still_works(self, mock_card_fetcher_class, mock_client_factory):
        """Test update_prices flag still works as before."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_factory.return_value = mock_client
        mock_card_fetcher = MagicMock()
        mock_card_fetcher_class.return_value = mock_card_fetcher
        
        # Create config with update_prices=True
        config = ProcessorConfig(update_prices=True)
        processor = MagicCardProcessor(config)
        
        self.assertTrue(processor.update_prices)


if __name__ == "__main__":
    unittest.main()
