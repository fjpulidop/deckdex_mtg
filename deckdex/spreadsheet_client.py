import gspread
from loguru import logger
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
            logger.info(f"Error occurred while authorizing Google Sheets client: {e}")

    def get_empty_row_index_to_start(self, col_num: int) -> int:
        """Get the first empty row index in the specified column."""
        try:
            col_values = self.sheet.col_values(col_num)
            return len(col_values) + 1
        except Exception as e:
            logger.info(f"Error occurred while getting empty row index: {e}")
            return None

    def get_cards(self):
        try:
            return self.sheet.get_all_values()
        except Exception as e:
            logger.info(f"Error occurred while getting card names: {e}")
            return []

    def update_cells(self, start, end, data):
        try:
            self.sheet.update("{}:{}".format(start, end), data)
        except Exception as e:
            logger.info(f"Error occurred while updating cells: {e}")

    def get_all_cards_prices(self):
        try:
            # First get all values from the sheet
            all_values = self.sheet.get_all_values()
            # The first row contains column names
            columns = all_values[0]
            # Find the column index that matches the column_name
            column_index = columns.index("Price")
            # Get all the cards from the specified column
            cards = [
                [row[1], row[column_index]] for row in all_values[1:]
            ]  # Exclude header row
            return cards
        except Exception as e:
            logger.info(f"Error occurred while getting cards from column: {e}")
            return []

    def update_column(self, column_name, data):
        try:
            # First get all values from the sheet
            all_values = self.sheet.get_all_values()
            # The first row contains column names
            columns = all_values[0]
            # Find the column index that matches the column_name
            column_index = columns.index(column_name)
            # Get current values of the column
            current_rows = [
                [row[1], row[column_index]] for row in all_values[1:]
            ]  # excluding header row
            # Iterate over the data and update the corresponding cell in the column if the value has changed
            for i, (new_value, current_row) in enumerate(
                zip(data, current_rows), start=2
            ):  # starting from 2 to avoid the header
                if current_row[1] is not None:
                    if str(new_value) != str.replace(
                        current_row[1], " €", ""
                    ):  # update only if the value has changed
                        self.sheet.update_cell(
                            i, column_index + 1, new_value
                        )  # +1 because gspread uses 1-indexing
                        logger.info(
                            f"The price of the card: {current_row[0]} was updated."
                        )

        except Exception as e:
            logger.info(f"Error occurred while updating column: {e}")
