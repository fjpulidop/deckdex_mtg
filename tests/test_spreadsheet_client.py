import unittest
from unittest.mock import patch, MagicMock
from deckdex.spreadsheet_client import SpreadsheetClient
from oauth2client.service_account import ServiceAccountCredentials


class TestSpreadsheetClient(unittest.TestCase):
    @patch("gspread.authorize")
    @patch.object(ServiceAccountCredentials, "from_json_keyfile_name")
    def setUp(self, mock_from_json_keyfile_name, mock_authorize):
        mock_from_json_keyfile_name.return_value = MagicMock()
        mock_authorize.return_value.open.return_value.worksheet.return_value = (
            MagicMock()
        )
        self.spreadsheet_client = SpreadsheetClient(
            "test_credentials.json", "test_spreadsheet", "test_worksheet"
        )

    def test_init(self):
        self.assertIsNotNone(self.spreadsheet_client.creds)
        self.assertIsNotNone(self.spreadsheet_client.client)
        self.assertIsNotNone(self.spreadsheet_client.sheet)

    @patch.object(SpreadsheetClient, "get_empty_row_index_to_start")
    def test_get_empty_row_index_to_start(self, mock_get_empty_row):
        mock_get_empty_row.return_value = 10
        result = self.spreadsheet_client.get_empty_row_index_to_start(1)
        self.assertEqual(result, 10)

    @patch.object(SpreadsheetClient, "get_cards")
    def test_get_cards(self, mock_get_cards):
        mock_get_cards.return_value = ["card1", "card2", "card3"]
        result = self.spreadsheet_client.get_cards()
        self.assertEqual(result, ["card1", "card2", "card3"])

    @patch.object(SpreadsheetClient, "update_cells")
    def test_update_cells(self, mock_update_cells):
        mock_update_cells.return_value = None
        result = self.spreadsheet_client.update_cells("A1", "B1", [["data"]])
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
