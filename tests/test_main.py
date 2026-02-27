#!/usr/bin/env python
"""Test suite for DeckDex MTG main CLI and configuration."""

import unittest
from unittest.mock import patch, MagicMock
from deckdex.config import (
    ProcessorConfig, ClientFactory,
    ProcessingConfig, ScryfallConfig, OpenAIConfig, GoogleSheetsConfig,
)
from deckdex.magic_card_processor import MagicCardProcessor
from deckdex.dry_run_client import DryRunClient


class TestProcessorConfig(unittest.TestCase):
    """Test suite for ProcessorConfig dataclass."""

    def test_config_creation_with_defaults(self):
        """Test ProcessorConfig creation with default values."""
        config = ProcessorConfig()

        # Behavioral flags
        self.assertFalse(config.openai.enabled)
        self.assertFalse(config.update_prices)
        self.assertFalse(config.dry_run)
        self.assertFalse(config.verbose)

        # Performance settings (via nested sub-configs)
        self.assertEqual(config.processing.batch_size, 20)
        self.assertEqual(config.processing.max_workers, 4)
        self.assertEqual(config.processing.api_delay, 0.1)
        self.assertEqual(config.scryfall.max_retries, 3)

        # Google Sheets settings
        self.assertIsNone(config.credentials_path)
        self.assertEqual(config.google_sheets.sheet_name, "magic")
        self.assertEqual(config.google_sheets.worksheet_name, "cards")

        # Processing control
        self.assertIsNone(config.limit)
        self.assertIsNone(config.resume_from)

    def test_config_creation_with_custom_values(self):
        """Test ProcessorConfig creation with custom values."""
        config = ProcessorConfig(
            openai=OpenAIConfig(enabled=True),
            processing=ProcessingConfig(batch_size=50, max_workers=8, api_delay=0.2),
            limit=100,
            resume_from=50,
        )

        self.assertTrue(config.openai.enabled)
        self.assertEqual(config.processing.batch_size, 50)
        self.assertEqual(config.processing.max_workers, 8)
        self.assertEqual(config.processing.api_delay, 0.2)
        self.assertEqual(config.limit, 100)
        self.assertEqual(config.resume_from, 50)

    def test_config_validation_invalid_batch_size(self):
        """Test ProcessorConfig validation for invalid batch_size."""
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(processing=ProcessingConfig(batch_size=0))
        self.assertIn("batch_size must be > 0", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(processing=ProcessingConfig(batch_size=-5))
        self.assertIn("batch_size must be > 0", str(cm.exception))

    def test_config_validation_invalid_max_workers(self):
        """Test ProcessorConfig validation for invalid max_workers."""
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(processing=ProcessingConfig(max_workers=0))
        self.assertIn("max_workers must be between 1 and 10", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(processing=ProcessingConfig(max_workers=15))
        self.assertIn("max_workers must be between 1 and 10", str(cm.exception))

    def test_config_validation_invalid_api_delay(self):
        """Test ProcessorConfig validation for invalid api_delay."""
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(processing=ProcessingConfig(api_delay=-0.1))
        self.assertIn("api_delay must be >= 0", str(cm.exception))

    def test_config_validation_invalid_max_retries(self):
        """Test ProcessorConfig validation for invalid max_retries."""
        with self.assertRaises(ValueError) as cm:
            ProcessorConfig(scryfall=ScryfallConfig(max_retries=0))
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
    @patch("os.path.isfile", return_value=True)
    @patch.dict("os.environ", {"GOOGLE_API_CREDENTIALS": "/path/to/creds.json"})
    def test_factory_returns_spreadsheet_client_when_dry_run_false(self, mock_isfile, mock_spreadsheet_class):
        """Test ClientFactory returns SpreadsheetClient when dry_run=False."""
        config = ProcessorConfig(dry_run=False)

        client = ClientFactory.create_spreadsheet_client(config)

        mock_spreadsheet_class.assert_called_once_with(
            "/path/to/creds.json",
            config.google_sheets,
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
        mock_client_factory.return_value = MagicMock()
        mock_card_fetcher_class.return_value = MagicMock()

        config = ProcessorConfig(
            processing=ProcessingConfig(batch_size=50, max_workers=8, api_delay=0.2),
            scryfall=ScryfallConfig(max_retries=10),
        )
        processor = MagicCardProcessor(config)

        self.assertEqual(processor.config.processing.batch_size, 50)
        self.assertEqual(processor.config.processing.max_workers, 8)
        self.assertEqual(processor.config.processing.api_delay, 0.2)
        self.assertEqual(processor.config.scryfall.max_retries, 10)

        mock_card_fetcher_class.assert_called_once_with(
            scryfall_config=config.scryfall,
            openai_config=config.openai,
        )


class TestBackwardsCompatibility(unittest.TestCase):
    """Test suite for backwards compatibility."""

    @patch("deckdex.config.ClientFactory.create_spreadsheet_client")
    @patch("deckdex.magic_card_processor.CardFetcher")
    def test_default_config_matches_old_behavior(self, mock_card_fetcher_class, mock_client_factory):
        """Test default config values match old hardcoded constants."""
        mock_client_factory.return_value = MagicMock()
        mock_card_fetcher_class.return_value = MagicMock()

        config = ProcessorConfig()
        processor = MagicCardProcessor(config)

        self.assertEqual(processor.config.processing.batch_size, 20)   # Old BATCH_SIZE
        self.assertEqual(processor.config.processing.max_workers, 4)   # Old hardcoded value
        self.assertEqual(processor.config.scryfall.max_retries, 3)     # Current default
        # Note: api_delay changed from 0.05 to 0.1 (intentional improvement)

    @patch("deckdex.config.ClientFactory.create_spreadsheet_client")
    @patch("deckdex.magic_card_processor.CardFetcher")
    def test_use_openai_flag_still_works(self, mock_card_fetcher_class, mock_client_factory):
        """Test use_openai flag still works via openai.enabled."""
        mock_client_factory.return_value = MagicMock()
        mock_card_fetcher_class.return_value = MagicMock()

        config = ProcessorConfig(openai=OpenAIConfig(enabled=True))
        processor = MagicCardProcessor(config)

        self.assertTrue(processor.config.openai.enabled)

    @patch("deckdex.config.ClientFactory.create_spreadsheet_client")
    @patch("deckdex.magic_card_processor.CardFetcher")
    def test_update_prices_flag_still_works(self, mock_card_fetcher_class, mock_client_factory):
        """Test update_prices flag still works as before."""
        mock_client_factory.return_value = MagicMock()
        mock_card_fetcher_class.return_value = MagicMock()

        config = ProcessorConfig(update_prices=True)
        processor = MagicCardProcessor(config)

        self.assertTrue(processor.update_prices)


if __name__ == "__main__":
    unittest.main()
