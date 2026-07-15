import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from mypythonlibrary import aimodule
from mypythonlibrary import summarize_news
from mypythonlibrary.dataloader import CSVLoader


class AimoduleTests(unittest.TestCase):
    def test_ask_question_uses_user_input_when_prompt_missing(self):
        with patch("mypythonlibrary.aimodule.AIClient") as mock_client:
            mock_client.return_value.ask.return_value = "done"

            with patch("builtins.input", return_value="Write me a summary"):
                result = aimodule.ask_question()

        self.assertEqual(result, "done")
        mock_client.return_value.ask.assert_called_once_with(
            "Write me a summary",
            system="You are a helpful assistant. Respond in English only, clearly and concisely.",
        )

    def test_summarize_news_pipes_loader_results_to_ai(self):
        loader = MagicMock()
        loader.build_filters.return_value = {"company": "Acme"}
        loader.apply_keyword.return_value = {"company": "Acme"}
        loader.get_fields.return_value = [{"headline": "Acme announces merger"}]

        with patch("mypythonlibrary.CSVLoader", return_value=loader):
            with patch("mypythonlibrary.ask_question", return_value="summary") as mock_ai:
                result = summarize_news()

        self.assertEqual(result, "summary")
        mock_ai.assert_called_once()
        self.assertIn("Acme", mock_ai.call_args.kwargs["prompt"])

    def test_summarize_news_formats_prompt_with_clear_sections(self):
        loader = MagicMock()
        loader.build_filters.return_value = {"company": "Acme"}
        loader.apply_keyword.return_value = {"company": "Acme"}
        loader.get_fields.return_value = [{"headline": "Acme announces merger"}]

        with patch("mypythonlibrary.CSVLoader", return_value=loader):
            with patch("mypythonlibrary.ask_question", return_value="summary") as mock_ai:
                summarize_news()

        prompt = mock_ai.call_args.kwargs["prompt"]
        self.assertIn("Instructions:", prompt)
        self.assertIn("User filters:", prompt)
        self.assertIn("News items:", prompt)
        self.assertLess(prompt.index("Instructions:"), prompt.index("User filters:"))
        self.assertLess(prompt.index("User filters:"), prompt.index("News items:"))

    def test_get_fields_can_return_source_and_url(self):
        loader = CSVLoader.__new__(CSVLoader)
        loader.df = pd.DataFrame([
            {"id": "1", "company": "Acme", "date": "2026-07-13", "headline": "Acme announces merger", "source": "Yahoo Finance", "url": "https://example.com/story"}
        ])
        loader.ask = MagicMock(return_value="5 6")

        result = loader.get_fields({})

        self.assertEqual(result[0]["source"], "Yahoo Finance")
        self.assertEqual(result[0]["url"], "https://example.com/story")

    def test_summarize_news_prompt_mentions_yahoo_and_url_context(self):
        loader = MagicMock()
        loader.build_filters.return_value = {"company": "Acme"}
        loader.apply_keyword.return_value = {"company": "Acme"}
        loader.get_fields.return_value = [{
            "headline": "Acme announces merger",
            "source": "Yahoo Finance",
            "url": "https://example.com/story",
        }]

        with patch("mypythonlibrary.CSVLoader", return_value=loader):
            with patch("mypythonlibrary.ask_question", return_value="summary") as mock_ai:
                summarize_news()

        prompt = mock_ai.call_args.kwargs["prompt"]
        self.assertIn("source and the article URL", prompt)
        self.assertIn("Yahoo", prompt)
        self.assertIn("https://example.com/story", prompt)


if __name__ == "__main__":
    unittest.main()
