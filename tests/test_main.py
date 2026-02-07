import argparse
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to sys.path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import main
from deckdex.magic_card_processor import MagicCardProcessor


class TestMain(unittest.TestCase):
    """Test suite for main module."""

    @patch("main.MagicCardProcessor")
    @patch("main.get_args")
    def test_process_card_data_with_openai(self, mock_get_args, mock_processor_class):
        """Test processing card data with OpenAI enabled."""
        # Configure the mock args
        mock_args = MagicMock()
        mock_args.use_openai = True
        mock_args.update_prices = False
        mock_get_args.return_value = mock_args
        
        # Create the MagicCardProcessor mock
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        
        # Call the main function
        main()

        # Check that the mock objects were used correctly
        mock_processor_class.assert_called_once_with(True, False)
        mock_processor.process_card_data.assert_called_once()

    @patch("main.MagicCardProcessor")
    @patch("main.get_args")
    def test_process_card_data_without_openai(self, mock_get_args, mock_processor_class):
        """Test processing card data without OpenAI."""
        # Configure the mock args
        mock_args = MagicMock()
        mock_args.use_openai = False
        mock_args.update_prices = False
        mock_get_args.return_value = mock_args
        
        # Create the MagicCardProcessor mock
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        
        # Call the main function
        main()

        # Check that the mock objects were used correctly
        mock_processor_class.assert_called_once_with(False, False)
        mock_processor.process_card_data.assert_called_once()

    @patch("main.MagicCardProcessor")
    @patch("main.get_args")
    def test_main_with_update_prices(self, mock_get_args, mock_processor_class):
        """
        Test the main function with update_prices flag.

        This test checks whether the main function correctly initializes the
        MagicCardProcessor objects and correctly calls the
        process_card_data function with them.
        """
        # Configure the mock args
        mock_args = MagicMock()
        mock_args.use_openai = False
        mock_args.update_prices = True
        mock_get_args.return_value = mock_args
        
        # Create the MagicCardProcessor mock
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        
        # Call the main function
        main()

        # Verify that the methods were called correctly
        mock_processor_class.assert_called_once_with(False, True)
        mock_processor.process_card_data.assert_called_once()

    def test_magic_card_processor_initialization(self):
        """Test the initialization of MagicCardProcessor."""
        # Mock the dependencies
        with patch("deckdex.magic_card_processor.CardFetcher") as mock_card_fetcher_class:
            with patch("deckdex.magic_card_processor.SpreadsheetClient") as mock_spreadsheet_client_class:
                # Create a mock for the credential file path
                with patch("deckdex.magic_card_processor.os.getenv", return_value="test_credentials.json"):
                    # Initialize the processor
                    processor = MagicCardProcessor(use_openai=False, update_prices=True)
                    
                    # Verify that the dependencies were initialized correctly
                    mock_card_fetcher_class.assert_called_once()
                    mock_spreadsheet_client_class.assert_called_once_with(
                        "test_credentials.json", "magic", "cards"
                    )
                    
                    # Verify the processor attributes
                    self.assertFalse(processor.use_openai)
                    self.assertTrue(processor.update_prices)
                    self.assertEqual(processor.error_count, 0)
                    self.assertEqual(processor.last_error_count, 0)
                    self.assertEqual(processor.not_found_cards, [])


if __name__ == "__main__":
    unittest.main()
