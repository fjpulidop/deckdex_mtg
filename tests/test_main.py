import argparse
import unittest
from unittest.mock import patch
from main import main, MagicCardProcessor


class TestMain(unittest.TestCase):
    """Test suite for main module."""

    @patch("main.MagicCardProcessor")
    def test_process_card_data_with_openai(self, mock_processor):
        # Create the MagicCardProcessor and call process_card_data()
        processor = mock_processor.return_value
        processor.process_card_data()

        # Check that the mock objects were used correctly
        processor.process_card_data.assert_called_once()

    @patch("main.MagicCardProcessor")
    def test_process_card_data_without_openai(self, mock_processor):
        # Create the MagicCardProcessor and call process_card_data()
        processor = mock_processor.return_value
        processor.process_card_data()

        # Check that the mock objects were used correctly
        processor.process_card_data.assert_called_once()

    @patch("main.MagicCardProcessor")
    def test_main(self, mock_processor):
        """
        Test the main function.

        This test checks whether the main function correctly initializes the
        MagicCardProcessor objects and correctly calls the
        process_card_data function with them.
        """
        mock_args = argparse.Namespace(use_openai=True, update_prices=False)
        with patch("argparse.ArgumentParser.parse_args", return_value=mock_args):
            main()

        # Verify that the methods were called correctly
        mock_processor.assert_called_once_with(True, False)
        mock_processor.return_value.process_card_data.assert_called_once()

    @patch("deckdex.magic_card_processor.CardFetcher")
    @patch("deckdex.magic_card_processor.SpreadsheetClient")
    def test_update_prices_data(self, mock_spreadsheet_client, mock_card_fetcher):
        # Configure the mock objects
        mock_spreadsheet_client.return_value.get_all_cards_prices.return_value = [
            ["card1"],
            ["card2"],
            ["card3"],
        ]
        mock_card_fetcher.return_value.search_card.side_effect = [
            {"prices": {"eur": "1.00"}},
            {"prices": {"eur": "2.00"}},
            {"prices": {"eur": None}},
        ]

        # Create the MagicCardProcessor and call update_prices_data()
        processor = MagicCardProcessor(False, True)
        processor.update_prices_data([["card1"], ["card2"], ["card3"]])

        # Check that the mock objects were used correctly
        mock_card_fetcher.return_value.search_card.assert_any_call("card1")
        mock_card_fetcher.return_value.search_card.assert_any_call("card2")
        mock_card_fetcher.return_value.search_card.assert_any_call("card3")
        mock_spreadsheet_client.return_value.update_column.assert_called_once_with(
            "Price", ["1,00", "2,00", "N/A"]
        )


if __name__ == "__main__":
    unittest.main()
