import unittest
from unittest.mock import patch, MagicMock
from openai import OpenAI
from deckdex.card_fetcher import CardFetcher
from deckdex.config import ScryfallConfig, OpenAIConfig


class TestCardFetcher(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        self.card_fetcher = CardFetcher(
            scryfall_config=ScryfallConfig(),
            openai_config=OpenAIConfig(),
        )

    @patch.object(CardFetcher, "_make_request")
    def test_search_card(self, mock_make_request):
        """Test searching for a card by name."""
        mock_make_request.return_value = {"name": "Test Card"}
        
        # Mock the individual search methods
        with patch.object(CardFetcher, "_exact_match_search", return_value={"name": "Test Card"}):
            result = self.card_fetcher.search_card("Test Card")
            self.assertEqual(result, {"name": "Test Card"})

    @patch.object(CardFetcher, "_call_openai")
    def test_get_card_info_with_openai(self, mock_call_openai):
        """Test getting card information with OpenAI analysis."""
        # Configure the mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"strategy": "This is a test strategy.", "tier": "A"}'
        mock_call_openai.return_value = mock_response
        
        # Set up mock OpenAI client
        self.card_fetcher.openai_client = MagicMock()
        
        # Mock the search_card method
        with patch.object(CardFetcher, "search_card", return_value={"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}):
            result = self.card_fetcher.get_card_info("Test Card")
            
            # Verify the result
            self.assertEqual(result, ({"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}, "This is a test strategy.", "A"))
            
            # Verify that _call_openai was called
            mock_call_openai.assert_called_once()

    @patch.object(CardFetcher, "_exact_match_search")
    @patch.object(CardFetcher, "_fuzzy_match_search")
    def test_search_card_with_fuzzy_match(self, mock_fuzzy_search, mock_exact_search):
        """Test searching for a card with fuzzy matching."""
        # First search fails, second succeeds
        mock_exact_search.return_value = None
        mock_fuzzy_search.return_value = {"name": "Test Card"}
        
        result = self.card_fetcher.search_card("Test Crd")  # Misspelled name
        self.assertEqual(result, {"name": "Test Card"})
        
        # Verify both methods were called
        mock_exact_search.assert_called_once_with("Test Crd")
        mock_fuzzy_search.assert_called_once_with("Test Crd")

    @patch.object(CardFetcher, "_make_request")
    def test_exact_match_search(self, mock_make_request):
        """Test the exact match search method."""
        mock_make_request.return_value = {"name": "Test Card"}
        
        result = self.card_fetcher._exact_match_search("Test Card")
        self.assertEqual(result, {"name": "Test Card"})
        
        # Verify the URL
        expected_url = f"{CardFetcher.BASE_URL}/cards/named?exact=Test Card"
        mock_make_request.assert_called_once_with(expected_url)

    @patch.object(CardFetcher, "_make_request")
    def test_fuzzy_match_search(self, mock_make_request):
        """Test the fuzzy match search method."""
        mock_make_request.return_value = {"name": "Test Card"}
        
        result = self.card_fetcher._fuzzy_match_search("Test Crd")
        self.assertEqual(result, {"name": "Test Card"})
        
        # Verify the URL
        expected_url = f"{CardFetcher.BASE_URL}/cards/named?fuzzy=Test Crd"
        mock_make_request.assert_called_once_with(expected_url)

    @patch.object(CardFetcher, "_call_openai")
    def test_get_card_info_malformed_json(self, mock_call_openai):
        """Test handling of malformed JSON response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'Invalid JSON{'
        mock_call_openai.return_value = mock_response
        
        self.card_fetcher.openai_client = MagicMock()
        
        with patch.object(CardFetcher, "search_card", return_value={"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}):
            result = self.card_fetcher.get_card_info("Test Card")
            self.assertEqual(result, ({"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}, None, None))

    @patch.object(CardFetcher, "_call_openai")
    def test_get_card_info_invalid_tier(self, mock_call_openai):
        """Test validation of invalid tier value."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"strategy": "Test strategy", "tier": "Z"}'
        mock_call_openai.return_value = mock_response
        
        self.card_fetcher.openai_client = MagicMock()
        
        with patch.object(CardFetcher, "search_card", return_value={"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}):
            result = self.card_fetcher.get_card_info("Test Card")
            # Tier should be None because Z is invalid
            self.assertEqual(result, ({"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}, "Test strategy", None))

    @patch.object(CardFetcher, "_call_openai")
    def test_get_card_info_missing_tier(self, mock_call_openai):
        """Test handling of missing tier key in JSON response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"strategy": "Test strategy"}'
        mock_call_openai.return_value = mock_response
        
        self.card_fetcher.openai_client = MagicMock()
        
        with patch.object(CardFetcher, "search_card", return_value={"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}):
            result = self.card_fetcher.get_card_info("Test Card")
            # Tier should be None because it's missing
            self.assertEqual(result, ({"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}, "Test strategy", None))

    @patch.object(CardFetcher, "_call_openai")
    def test_get_card_info_missing_strategy(self, mock_call_openai):
        """Test handling of missing strategy key in JSON response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"tier": "A"}'
        mock_call_openai.return_value = mock_response
        
        self.card_fetcher.openai_client = MagicMock()
        
        with patch.object(CardFetcher, "search_card", return_value={"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}):
            result = self.card_fetcher.get_card_info("Test Card")
            # Strategy should be None because it's missing
            self.assertEqual(result, ({"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}, None, "A"))

    @patch.object(CardFetcher, "_call_openai")
    def test_get_card_info_strategy_truncation(self, mock_call_openai):
        """Test truncation of strategy text exceeding 500 characters."""
        long_strategy = "A" * 600  # 600 characters
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = f'{{"strategy": "{long_strategy}", "tier": "B"}}'
        mock_call_openai.return_value = mock_response
        
        self.card_fetcher.openai_client = MagicMock()
        
        with patch.object(CardFetcher, "search_card", return_value={"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}):
            result = self.card_fetcher.get_card_info("Test Card")
            # Strategy should be truncated to 500 chars
            self.assertEqual(len(result[1]), 500)
            self.assertEqual(result[2], "B")

    @patch.object(CardFetcher, "_call_openai")
    def test_get_card_info_rate_limit_error(self, mock_call_openai):
        """Test handling of RateLimitError after retries exhausted."""
        from openai import RateLimitError
        mock_call_openai.side_effect = RateLimitError("Rate limit exceeded", response=MagicMock(), body=None)
        
        self.card_fetcher.openai_client = MagicMock()
        
        with patch.object(CardFetcher, "search_card", return_value={"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}):
            result = self.card_fetcher.get_card_info("Test Card")
            self.assertEqual(result, ({"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}, None, None))

    @patch.object(CardFetcher, "_call_openai")
    def test_get_card_info_authentication_error(self, mock_call_openai):
        """Test handling of AuthenticationError (no retry)."""
        from openai import AuthenticationError
        mock_call_openai.side_effect = AuthenticationError("Invalid API key", response=MagicMock(), body=None)
        
        self.card_fetcher.openai_client = MagicMock()
        
        with patch.object(CardFetcher, "search_card", return_value={"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}):
            result = self.card_fetcher.get_card_info("Test Card")
            self.assertEqual(result, ({"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}, None, None))

    @patch.object(CardFetcher, "_call_openai")
    def test_get_card_info_invalid_request_error(self, mock_call_openai):
        """Test handling of BadRequestError (no retry)."""
        from openai import BadRequestError
        mock_call_openai.side_effect = BadRequestError("Invalid request", response=MagicMock(), body=None)
        
        self.card_fetcher.openai_client = MagicMock()
        
        with patch.object(CardFetcher, "search_card", return_value={"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}):
            result = self.card_fetcher.get_card_info("Test Card")
            self.assertEqual(result, ({"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}, None, None))

    @patch.object(CardFetcher, "_call_openai")
    def test_get_card_info_api_connection_error(self, mock_call_openai):
        """Test handling of APIConnectionError."""
        from openai import APIConnectionError
        mock_call_openai.side_effect = APIConnectionError(request=MagicMock())
        
        self.card_fetcher.openai_client = MagicMock()
        
        with patch.object(CardFetcher, "search_card", return_value={"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}):
            result = self.card_fetcher.get_card_info("Test Card")
            self.assertEqual(result, ({"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}, None, None))

    @patch.object(CardFetcher, "_call_openai")
    def test_get_card_info_api_error(self, mock_call_openai):
        """Test handling of generic APIError."""
        from openai import APIError
        mock_call_openai.side_effect = APIError("Server error", request=MagicMock(), body=None)
        
        self.card_fetcher.openai_client = MagicMock()
        
        with patch.object(CardFetcher, "search_card", return_value={"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}):
            result = self.card_fetcher.get_card_info("Test Card")
            self.assertEqual(result, ({"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}, None, None))


if __name__ == "__main__":
    unittest.main()
