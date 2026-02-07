import unittest
from unittest.mock import patch, MagicMock
import openai
from deckdex.card_fetcher import CardFetcher


class TestCardFetcher(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        self.card_fetcher = CardFetcher()

    @patch.object(CardFetcher, "_make_request")
    def test_search_card(self, mock_make_request):
        """Test searching for a card by name."""
        mock_make_request.return_value = {"name": "Test Card"}
        
        # Mock the individual search methods
        with patch.object(CardFetcher, "_exact_match_search", return_value={"name": "Test Card"}):
            result = self.card_fetcher.search_card("Test Card")
            self.assertEqual(result, {"name": "Test Card"})

    @patch("openai.Completion.create")
    def test_get_card_info_with_openai(self, mock_openai_create):
        """Test getting card information with OpenAI analysis."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].text = "Strategy: This is a test strategy.\nTier: A"
        mock_openai_create.return_value = mock_response
        
        # Set up the OpenAI API key
        self.card_fetcher.openai_api_key = "test_key"
        
        # Mock the search_card method
        with patch.object(CardFetcher, "search_card", return_value={"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}):
            result = self.card_fetcher.get_card_info("Test Card")
            
            # Verify the result
            self.assertEqual(result, ({"name": "Test Card", "type_line": "Creature", "oracle_text": "Test text"}, "This is a test strategy.", "A"))
            
            # Verify that openai.Completion.create was called
            mock_openai_create.assert_called_once()

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


if __name__ == "__main__":
    unittest.main()
