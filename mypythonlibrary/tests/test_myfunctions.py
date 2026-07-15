import tempfile
import unittest
from pathlib import Path

import pandas as pd

from mypythonlibrary import dataloader


class MyFunctionsTests(unittest.TestCase):
    def test_load_headlines_reads_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "headlines.csv"
            sample_df = pd.DataFrame(
                [
                    {"id": "1", "company": "Acme", "date": "2024-01-01", "headline": "Acme earnings rise"},
                    {"id": "2", "company": "Beta", "date": "2024-01-02", "headline": "Beta launches product"},
                ]
            )
            sample_df.to_csv(csv_path, index=False)

            result = dataloader.load_headlines(csv_path)

            self.assertEqual(list(result.columns), ["id", "company", "date", "headline"])
            self.assertEqual(len(result), 2)

    def test_load_headlines_uses_default_data_file(self):
        result = dataloader.load_headlines()

        self.assertIn("headline", result.columns)
        self.assertGreater(len(result), 0)

    def test_find_records_filters_case_insensitively(self):
        df = pd.DataFrame(
            [
                {"id": "1", "company": "Acme", "date": "2024-01-01", "headline": "Acme earnings rise"},
                {"id": "2", "company": "Beta", "date": "2024-01-02", "headline": "Beta launches product"},
            ]
        )

        result = dataloader.find_records(df, company="acme")

        self.assertEqual(result["id"].tolist(), ["1"])

    def test_find_headline_uses_optional_filters(self):
        df = pd.DataFrame(
            [
                {"id": "1", "company": "Acme", "date": "2024-01-01", "headline": "Acme earnings rise"},
                {"id": "2", "company": "Beta", "date": "2024-01-02", "headline": "Beta launches product"},
            ]
        )

        result = dataloader.find_headline(df, company="Acme", headline="earnings")

        self.assertEqual(result["id"].tolist(), ["1"])


if __name__ == "__main__":
    unittest.main()
