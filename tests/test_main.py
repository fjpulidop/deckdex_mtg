import argparse
import unittest
from unittest.mock import patch
from main import process_card_data, main


class TestMain(unittest.TestCase):
    """Test suite for main module."""

    @patch("main.CardFetcher")
    @patch("main.SpreadsheetClient")
    def test_process_card_data_with_openai(self, mock_card_fetcher, mock_spreadsheet_client):
        # Configure the mock objects
        mock_spreadsheet_client.return_value.get_cards.return_value = [
            ["card1"],
            ["card2"],
            ["card3"],
        ]
        mock_spreadsheet_client.return_value.get_empty_row_index_to_start.return_value = (
            1  # <-- Esto es nuevo
        )
        mock_card_fetcher.return_value.get_card_info.return_value = (None, None, None)

        # Call the function
        process_card_data(
            mock_card_fetcher.return_value, mock_spreadsheet_client.return_value, True
        )

        # Check that the mock objects were used correctly
        mock_card_fetcher.return_value.get_card_info.assert_called()
        mock_spreadsheet_client.return_value.get_cards.assert_called()
        mock_spreadsheet_client.return_value.update_cells.assert_called()

    @patch("main.CardFetcher")
    @patch("main.SpreadsheetClient")
    def test_process_card_data_without_openai(self, mock_card_fetcher, mock_spreadsheet_client):
        # Configure the mock objects
        mock_spreadsheet_client.return_value.get_cards.return_value = [
            ["card1"],
            ["card2"],
            ["card3"],
        ]
        mock_spreadsheet_client.return_value.get_empty_row_index_to_start.return_value = (
            1  # <-- Esto es nuevo
        )
        mock_card_fetcher.return_value.get_card_info.return_value = (None, None, None)

        # Call the function
        process_card_data(
            mock_card_fetcher.return_value, mock_spreadsheet_client.return_value, False
        )

        # Check that the mock objects were used correctly
        mock_card_fetcher.return_value.get_card_info.assert_not_called()
        mock_spreadsheet_client.return_value.get_cards.assert_called()
        mock_spreadsheet_client.return_value.update_cells.assert_called()

    @patch("main.CardFetcher")
    @patch("main.SpreadsheetClient")
    @patch("main.process_card_data")
    def test_main(
        self, mock_process_card_data, mock_spreadsheet_client, mock_card_fetcher
    ):
        """
        Test the main function.

        This test checks whether the main function correctly initializes the
        CardFetcher and SpreadsheetClient objects and correctly calls the
        process_card_data function with them.
        """
        mock_args = argparse.Namespace(use_openai=True)
        with patch('argparse.ArgumentParser.parse_args', return_value=mock_args):
            main()

        # Verify that the methods were called correctly
        mock_card_fetcher.assert_called_once()
        mock_spreadsheet_client.assert_called_once()
        mock_process_card_data.assert_called_once_with(
            mock_card_fetcher.return_value, mock_spreadsheet_client.return_value, True
        )


if __name__ == "__main__":
    unittest.main()
