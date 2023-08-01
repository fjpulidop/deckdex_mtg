import gspread
from oauth2client.service_account import ServiceAccountCredentials


class SpreadsheetClient:
    def __init__(self, credential_file_path, spreadsheet_name, worksheet_name):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]
        try:
            self.creds = ServiceAccountCredentials.from_json_keyfile_name(
                credential_file_path, scope
            )
            self.client = gspread.authorize(self.creds)
            self.sheet = self.client.open(spreadsheet_name).worksheet(worksheet_name)
        except Exception as e:
            print(f"Error occurred while authorizing Google Sheets client: {e}")

    def get_empty_row_index_to_start(self, col_num: int) -> int:
        """Get the first empty row index in the specified column."""
        try:
            col_values = self.sheet.col_values(col_num)
            return len(col_values) + 1
        except Exception as e:
            print(f"Error occurred while getting empty row index: {e}")
            return None

    def get_cards(self):
        try:
            return self.sheet.get_all_values()
        except Exception as e:
            print(f"Error occurred while getting card names: {e}")
            return []

    def update_cells(self, start, end, data):
        try:
            self.sheet.update("{}:{}".format(start, end), data)
        except Exception as e:
            print(f"Error occurred while updating cells: {e}")
