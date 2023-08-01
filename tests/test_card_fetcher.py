import unittest
from unittest.mock import patch, MagicMock
import openai
from card_fetcher import CardFetcher


class TestCardFetcher(unittest.TestCase):
    def setUp(self):
        self.card_fetcher = CardFetcher()

    @patch("requests.get")
    def test_search_card(self, mock_get):
        mock_get.return_value.json.return_value = {"name": "Test Card"}
        mock_get.return_value.status_code = 200
        result = self.card_fetcher.search_card("Test Card")
        self.assertEqual(result, {"name": "Test Card"})

    @patch.object(openai.ChatCompletion, "create")
    def test_get_game_strategy(self, mock_create):
        mock_create.return_value = MagicMock(
            choices=[{"message": {"content": "Test Strategy"}}]
        )
        result = self.card_fetcher.get_game_strategy("Test Text")
        self.assertEqual(result, "Test Strategy")

    @patch.object(openai.ChatCompletion, "create")
    def test_get_tier(self, mock_create):
        mock_create.return_value = MagicMock(
            choices=[{"message": {"content": "Test Tier"}}]
        )
        result = self.card_fetcher.get_tier("Test Text", "1", "1", "1")
        self.assertEqual(result, "Test Tier")

    @patch.object(CardFetcher, "search_card")
    @patch.object(CardFetcher, "get_game_strategy")
    @patch.object(CardFetcher, "get_tier")
    def test_get_card_info(self, mock_tier, mock_strategy, mock_search):
        mock_search.return_value = {"name": "Test Card"}
        mock_strategy.return_value = "Test Strategy"
        mock_tier.return_value = "Test Tier"
        result = self.card_fetcher.get_card_info("Test Card")
        self.assertEqual(result, ({"name": "Test Card"}, "Test Strategy", "Test Tier"))


if __name__ == "__main__":
    unittest.main()
