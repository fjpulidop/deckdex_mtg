#!/usr/bin/env python
import os
import sys
from dotenv import load_dotenv
from deckdex.magic_card_processor import MagicCardProcessor
import unittest
from unittest.mock import patch, MagicMock

class TestCLI(unittest.TestCase):
    """Test suite for CLI functionality."""
    
    @patch("deckdex.magic_card_processor.SpreadsheetClient")
    @patch("deckdex.magic_card_processor.CardFetcher")
    def test_update_prices(self, mock_card_fetcher_class, mock_spreadsheet_client_class):
        """Test the price update functionality."""
        # Configure mocks
        mock_spreadsheet_client = MagicMock()
        mock_spreadsheet_client_class.return_value = mock_spreadsheet_client
        mock_spreadsheet_client.get_all_cards_prices.return_value = [["card1", "1,00"], ["card2", "2,00"]]
        
        mock_card_fetcher = MagicMock()
        mock_card_fetcher_class.return_value = mock_card_fetcher
        
        # Mock the update_prices_data method
        with patch.object(MagicCardProcessor, "update_prices_data") as mock_update_prices_data:
            # Create processor instance
            processor = MagicCardProcessor(use_openai=False, update_prices=True)
            
            # Get cards and update prices
            cards = processor.spreadsheet_client.get_all_cards_prices()
            processor.update_prices_data(cards)
            
            # Verify method calls
            mock_spreadsheet_client.get_all_cards_prices.assert_called_once()
            mock_update_prices_data.assert_called_once_with([["card1", "1,00"], ["card2", "2,00"]])
    
    @patch("deckdex.magic_card_processor.SpreadsheetClient")
    @patch("deckdex.magic_card_processor.CardFetcher")
    def test_process_cards(self, mock_card_fetcher_class, mock_spreadsheet_client_class):
        """Test the card processing functionality."""
        # Configure mocks
        mock_spreadsheet_client = MagicMock()
        mock_spreadsheet_client_class.return_value = mock_spreadsheet_client
        mock_spreadsheet_client.get_cards.return_value = [["card1"], ["card2"]]
        
        mock_card_fetcher = MagicMock()
        mock_card_fetcher_class.return_value = mock_card_fetcher
        
        # Mock the process_cards method
        with patch.object(MagicCardProcessor, "process_cards") as mock_process_cards:
            # Create processor instance
            processor = MagicCardProcessor(use_openai=False, update_prices=False)
            
            # Process cards
            processor.process_card_data()
            
            # Verify method calls
            mock_spreadsheet_client.get_cards.assert_called_once()
            mock_process_cards.assert_called_once_with([["card1"], ["card2"]])

if __name__ == "__main__":
    unittest.main() 