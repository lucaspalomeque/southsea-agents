"""Tests para content_generator.py — mock del LLM."""

import unittest
from unittest.mock import patch

from agents.writer.content_generator import generate_article, _parse_response
from agents.writer.tests.conftest import (
    SYNTHETIC_BRIEF,
    SYNTHETIC_VOICE,
    SYNTHETIC_FORMAT_ANALYSIS,
    SYNTHETIC_LLM_RESPONSE,
)


class TestParseResponse(unittest.TestCase):
    def test_parses_valid_response(self):
        result = _parse_response(SYNTHETIC_LLM_RESPONSE)

        self.assertIn("Layer 2", result["title"])
        self.assertIn("##", result["content"])
        self.assertLessEqual(len(result["excerpt"]), 280)
        self.assertTrue(len(result["content"]) > 0)

    def test_error_on_missing_delimiters(self):
        with self.assertRaises(ValueError):
            _parse_response("Just some text without delimiters")

    def test_error_on_empty_title(self):
        bad_response = "===TITLE===\n\n===CONTENT===\nSome content\n===EXCERPT===\nExcerpt"
        with self.assertRaises(ValueError) as ctx:
            _parse_response(bad_response)
        self.assertIn("título vacío", str(ctx.exception))

    def test_truncates_long_excerpt(self):
        long_excerpt = "A" * 300
        response = f"===TITLE===\nTítulo\n===CONTENT===\nContenido\n===EXCERPT===\n{long_excerpt}"
        result = _parse_response(response)
        self.assertLessEqual(len(result["excerpt"]), 280)
        self.assertTrue(result["excerpt"].endswith("..."))

    def test_content_has_markdown_sections(self):
        result = _parse_response(SYNTHETIC_LLM_RESPONSE)
        self.assertGreaterEqual(result["content"].count("##"), 2)


@patch("agents.writer.content_generator.completion")
class TestGenerateArticle(unittest.TestCase):
    def test_generates_article(self, mock_completion):
        mock_completion.return_value = SYNTHETIC_LLM_RESPONSE

        result = generate_article(
            brief=SYNTHETIC_BRIEF,
            voice=SYNTHETIC_VOICE,
            format_template=SYNTHETIC_FORMAT_ANALYSIS,
            format_name="analysis",
        )

        self.assertIn("title", result)
        self.assertIn("content", result)
        self.assertIn("excerpt", result)
        self.assertIn("Layer 2", result["title"])

        # Verify LLM was called with system prompt
        call_kwargs = mock_completion.call_args
        self.assertEqual(call_kwargs.kwargs.get("system"), SYNTHETIC_VOICE)

    def test_raises_on_bad_llm_response(self, mock_completion):
        mock_completion.return_value = "Garbage response without delimiters"

        with self.assertRaises(ValueError):
            generate_article(
                brief=SYNTHETIC_BRIEF,
                voice=SYNTHETIC_VOICE,
                format_template=SYNTHETIC_FORMAT_ANALYSIS,
                format_name="analysis",
            )


if __name__ == "__main__":
    unittest.main()
