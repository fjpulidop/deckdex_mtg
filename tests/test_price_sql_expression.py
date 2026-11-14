"""Regression tests: price_eur is text stored with a decimal comma ("0,08"); SQL must handle it."""

import re
import unittest
from unittest.mock import MagicMock

from deckdex.storage.repository import PRICE_NUMERIC_SQL, PostgresCollectionRepository


def _repo():
    return PostgresCollectionRepository("postgresql://u:p@localhost/db", engine=MagicMock())


class TestPriceNumericExpression(unittest.TestCase):
    def _regex(self):
        return re.search(r"~ '([^']+)'", PRICE_NUMERIC_SQL).group(1)

    def test_regex_accepts_comma_and_dot_decimals(self):
        pattern = self._regex()
        for value in ("0,08", "104,45", "1.00", "3", "12,5"):
            self.assertIsNotNone(re.match(pattern, value.replace(",", ".")), value)

    def test_regex_rejects_junk(self):
        pattern = self._regex()
        for value in ("N/A", "", "1.2.3", "abc", "-1"):
            self.assertIsNone(re.match(pattern, value), value)

    def test_comma_is_normalized_before_casting(self):
        self.assertIn("REPLACE(price_eur, ',', '.')", PRICE_NUMERIC_SQL)


class TestPriceFilters(unittest.TestCase):
    def test_price_filters_use_numeric_expression(self):
        where, params = _repo()._build_filter_clauses({"price_min": "1,5", "price_max": "10"}, None)
        self.assertEqual(where.count(PRICE_NUMERIC_SQL), 2)
        self.assertEqual(params["price_min"], 1.5)
        self.assertEqual(params["price_max"], 10.0)

    def test_sort_by_price_is_numeric(self):
        engine = MagicMock()
        conn = engine.connect.return_value.__enter__.return_value
        conn.execute.return_value.mappings.return_value.fetchall.return_value = []
        repo = PostgresCollectionRepository("postgresql://u:p@localhost/db", engine=engine)
        repo.get_cards_filtered(None, None, sort_by="price_eur", sort_dir="desc")
        sql = str(conn.execute.call_args[0][0])
        self.assertIn(f"ORDER BY {PRICE_NUMERIC_SQL} DESC", sql)


if __name__ == "__main__":
    unittest.main()
