"""Tests para writer_agent.py — mock completo del pipeline."""

import unittest
from unittest.mock import patch, MagicMock

from agents.writer.tests.conftest import (
    SYNTHETIC_BRIEF,
    SYNTHETIC_VOICE,
    SYNTHETIC_FORMATS,
)


MOCK_ARTICLE = {
    "title": "Test Article",
    "content": "## Section\nContent here",
    "excerpt": "Test excerpt for social media",
}

MOCK_SAVED_POST = {
    "id": "post-001",
    "title": "Test Article",
    "status": "pending_review",
}


@patch("agents.writer.writer_agent.translate_post")
@patch("agents.writer.writer_agent.update_brief_status")
@patch("agents.writer.writer_agent.save_post")
@patch("agents.writer.writer_agent.generate_article")
@patch("agents.writer.writer_agent.select_format")
@patch("agents.writer.writer_agent.fetch_pending_briefs")
@patch("agents.writer.writer_agent.load_formats")
@patch("agents.writer.writer_agent.load_voice")
class TestWriterAgent(unittest.TestCase):
    def _make_agent(self, mock_voice, mock_formats):
        mock_voice.return_value = SYNTHETIC_VOICE
        mock_formats.return_value = SYNTHETIC_FORMATS
        from agents.writer.writer_agent import WriterAgent
        return WriterAgent(batch_size=10, editorial_dir="editorial")

    def test_full_pipeline(
        self, mock_voice, mock_formats, mock_fetch, mock_select,
        mock_generate, mock_save, mock_update_brief, mock_translate,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch.return_value = [SYNTHETIC_BRIEF]
        mock_select.return_value = "analysis"
        mock_generate.return_value = MOCK_ARTICLE
        mock_save.return_value = MOCK_SAVED_POST
        mock_translate.return_value = True

        result = agent.run()

        self.assertEqual(len(result), 1)
        mock_select.assert_called_once()
        mock_generate.assert_called_once()
        mock_save.assert_called_once()
        mock_translate.assert_called_once_with("post-001")
        mock_update_brief.assert_called_once_with("brief-001", "processed")

        # Verify post data
        saved_post_arg = mock_save.call_args.args[0]
        self.assertEqual(saved_post_arg["status"], "pending_review")
        self.assertEqual(saved_post_arg["created_by"], "writer-agent")
        self.assertEqual(saved_post_arg["original_language"], "es")
        self.assertEqual(saved_post_arg["content_format"], "analysis")
        self.assertEqual(saved_post_arg["analyst_brief_id"], "brief-001")

    def test_empty_queue(
        self, mock_voice, mock_formats, mock_fetch, mock_select,
        mock_generate, mock_save, mock_update_brief, mock_translate,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch.return_value = []

        result = agent.run()

        self.assertEqual(result, [])
        mock_select.assert_not_called()

    def test_generation_failure_does_not_update_brief(
        self, mock_voice, mock_formats, mock_fetch, mock_select,
        mock_generate, mock_save, mock_update_brief, mock_translate,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch.return_value = [SYNTHETIC_BRIEF]
        mock_select.return_value = "analysis"
        mock_generate.side_effect = ValueError("LLM error")

        result = agent.run()

        self.assertEqual(result, [])
        mock_update_brief.assert_not_called()

    def test_save_failure_does_not_update_brief(
        self, mock_voice, mock_formats, mock_fetch, mock_select,
        mock_generate, mock_save, mock_update_brief, mock_translate,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch.return_value = [SYNTHETIC_BRIEF]
        mock_select.return_value = "analysis"
        mock_generate.return_value = MOCK_ARTICLE
        mock_save.side_effect = Exception("Supabase error")

        result = agent.run()

        self.assertEqual(result, [])
        mock_update_brief.assert_not_called()

    def test_translate_failure_still_updates_brief(
        self, mock_voice, mock_formats, mock_fetch, mock_select,
        mock_generate, mock_save, mock_update_brief, mock_translate,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch.return_value = [SYNTHETIC_BRIEF]
        mock_select.return_value = "analysis"
        mock_generate.return_value = MOCK_ARTICLE
        mock_save.return_value = MOCK_SAVED_POST
        mock_translate.return_value = False  # traducción falla

        result = agent.run()

        self.assertEqual(len(result), 1)
        mock_update_brief.assert_called_once_with("brief-001", "processed")

    def test_content_format_matches_selected(
        self, mock_voice, mock_formats, mock_fetch, mock_select,
        mock_generate, mock_save, mock_update_brief, mock_translate,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch.return_value = [SYNTHETIC_BRIEF]
        mock_select.return_value = "breaking"
        mock_generate.return_value = MOCK_ARTICLE
        mock_save.return_value = MOCK_SAVED_POST
        mock_translate.return_value = True

        agent.run()

        saved_post_arg = mock_save.call_args.args[0]
        self.assertEqual(saved_post_arg["content_format"], "breaking")

    def test_multiple_briefs_continues_on_error(
        self, mock_voice, mock_formats, mock_fetch, mock_select,
        mock_generate, mock_save, mock_update_brief, mock_translate,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        brief_2 = {**SYNTHETIC_BRIEF, "id": "brief-002", "title": "Second brief"}
        mock_fetch.return_value = [SYNTHETIC_BRIEF, brief_2]
        mock_select.return_value = "analysis"
        mock_generate.side_effect = [ValueError("fail"), MOCK_ARTICLE]
        mock_save.return_value = MOCK_SAVED_POST
        mock_translate.return_value = True

        result = agent.run()

        # First fails, second succeeds
        self.assertEqual(len(result), 1)
        mock_update_brief.assert_called_once_with("brief-002", "processed")


if __name__ == "__main__":
    unittest.main()
