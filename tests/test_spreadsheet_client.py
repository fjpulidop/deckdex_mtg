import unittest
from unittest.mock import patch, MagicMock
from deckdex.spreadsheet_client import SpreadsheetClient
from google.oauth2.service_account import Credentials


class TestSpreadsheetClient(unittest.TestCase):
    @patch("gspread.authorize")
    @patch.object(Credentials, "from_service_account_file")
    def setUp(self, mock_from_service_account_file, mock_authorize):
        # Configure the mocks
        mock_from_service_account_file.return_value = MagicMock()
        mock_worksheet = MagicMock()
        mock_worksheet.row_count = 100
        mock_client = MagicMock()
        mock_client.open.return_value.worksheet.return_value = mock_worksheet
        mock_authorize.return_value = mock_client
        
        # Create the client with mocks
        with patch.object(SpreadsheetClient, "_connect"):
            self.spreadsheet_client = SpreadsheetClient(
                "test_credentials.json", "test_spreadsheet", "test_worksheet"
            )
            # Manually assign the mocked objects
            self.spreadsheet_client._worksheet = mock_worksheet
            self.spreadsheet_client._client = mock_client

    def test_init(self):
        """Test the initialization of SpreadsheetClient."""
        self.assertIsNotNone(self.spreadsheet_client._client)
        self.assertIsNotNone(self.spreadsheet_client._worksheet)
        self.assertEqual(self.spreadsheet_client.credentials_path, "test_credentials.json")
        self.assertEqual(self.spreadsheet_client.spreadsheet_name, "test_spreadsheet")
        self.assertEqual(self.spreadsheet_client.worksheet_name, "test_worksheet")

    def test_get_empty_row_index_to_start(self):
        """Test getting the empty row index to start."""
        # Configure the mock for col_values
        self.spreadsheet_client._worksheet.col_values.return_value = ["header", "value1", "value2"]
        
        # Call the method
        result = self.spreadsheet_client.get_empty_row_index_to_start(1)
        
        # Verify the result
        self.assertEqual(result, 4)  # header + 2 values + 1 for the new row
        self.spreadsheet_client._worksheet.col_values.assert_called_once_with(1)

    def test_get_cards(self):
        """Test getting all cards."""
        # Configure the mock for get_all_values
        expected_values = [["header1", "header2"], ["value1", "value2"]]
        self.spreadsheet_client._worksheet.get_all_values.return_value = expected_values
        
        # Call the method
        result = self.spreadsheet_client.get_cards()
        
        # Verify the result
        self.assertEqual(result, expected_values)
        self.spreadsheet_client._worksheet.get_all_values.assert_called_once()

    def test_get_all_cards_prices(self):
        """Test getting all cards with their prices."""
        # Configure the mock for get_all_values
        worksheet_values = [
            ["Card Name", "Other", "Price", "More"],
            ["Card1", "Data1", "1,00", "Extra1"],
            ["Card2", "Data2", "2,00", "Extra2"]
        ]
        self.spreadsheet_client._worksheet.get_all_values.return_value = worksheet_values
        
        # Call the method
        result = self.spreadsheet_client.get_all_cards_prices()
        
        # Verify the result
        expected = [["Card1", "1,00"], ["Card2", "2,00"]]
        self.assertEqual(result, expected)
        self.spreadsheet_client._worksheet.get_all_values.assert_called_once()

    def test_update_cells(self):
        """Test updating cells in the worksheet."""
        # Configure the mock for update
        self.spreadsheet_client._worksheet.update.return_value = None
        
        # Call the method
        self.spreadsheet_client.update_cells("A1", "B2", [["data1"], ["data2"]])
        
        # Verify that the update method was called with the correct parameters
        self.spreadsheet_client._worksheet.update.assert_called_once_with("A1:B2", [["data1"], ["data2"]])

    @patch("time.sleep")  # Mock sleep to avoid delays in tests
    def test_update_column(self, mock_sleep):
        """Test updating a column in the worksheet."""
        # Configure the mocks
        self.spreadsheet_client._worksheet.row_values.return_value = ["Card Name", "Price", "Other"]
        
        # Mock the _batch_update_with_retry method
        with patch.object(SpreadsheetClient, "_batch_update_with_retry") as mock_batch_update:
            # Call the method with a small number of values
            self.spreadsheet_client.update_column("Price", ["1,00", "2,00"])
            
            # Verify that the batch update method was called
            mock_batch_update.assert_called_once()
            
            # Verify the column index was determined correctly
            self.spreadsheet_client._worksheet.row_values.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
