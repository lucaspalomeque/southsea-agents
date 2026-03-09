"""Tests para editor_agent.py — mock completo del pipeline."""

import unittest
from unittest.mock import patch, MagicMock

from agents.editor.tests.conftest import (
    SYNTHETIC_POST,
    SYNTHETIC_POST_REVISION_2,
    SYNTHETIC_POST_REVISION_3,
    SYNTHETIC_BRIEF,
    SYNTHETIC_VOICE,
    SYNTHETIC_FORMATS,
    SYNTHETIC_SAVED_REVIEW,
)


MOCK_EVALUATION_APPROVED = {
    "scores": {
        "voice_alignment": 8.0,
        "factual_rigor": 7.5,
        "format_compliance": 9.0,
        "thematic_alignment": 8.5,
    },
    "average_score": 8.25,
    "decision": "approved",
    "feedback": "Buen artículo.",
}

MOCK_EVALUATION_RETURNED = {
    "scores": {
        "voice_alignment": 8.0,
        "factual_rigor": 3.0,
        "format_compliance": 9.0,
        "thematic_alignment": 8.5,
    },
    "average_score": 7.12,
    "decision": "needs_revision",
    "feedback": "Rigor factual insuficiente.",
}


@patch("agents.editor.editor_agent.return_post")
@patch("agents.editor.editor_agent.approve_post")
@patch("agents.editor.editor_agent.save_review")
@patch("agents.editor.editor_agent.fetch_brief")
@patch("agents.editor.editor_agent.evaluate")
@patch("agents.editor.editor_agent.fetch_pending_posts")
@patch("agents.editor.editor_agent.load_formats")
@patch("agents.editor.editor_agent.load_voice")
class TestEditorAgent(unittest.TestCase):
    def _make_agent(self, mock_voice, mock_formats):
        mock_voice.return_value = SYNTHETIC_VOICE
        mock_formats.return_value = SYNTHETIC_FORMATS
        from agents.editor.editor_agent import EditorAgent
        return EditorAgent(batch_size=10, editorial_dir="editorial")

    def test_full_pipeline_approved(
        self, mock_voice, mock_formats, mock_fetch_posts, mock_evaluate,
        mock_fetch_brief, mock_save_review, mock_approve, mock_return,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch_posts.return_value = [SYNTHETIC_POST]
        mock_fetch_brief.return_value = SYNTHETIC_BRIEF
        mock_evaluate.return_value = MOCK_EVALUATION_APPROVED
        mock_save_review.return_value = SYNTHETIC_SAVED_REVIEW

        result = agent.run()

        self.assertEqual(len(result), 1)
        mock_evaluate.assert_called_once()
        mock_save_review.assert_called_once()
        mock_approve.assert_called_once_with("post-001")
        mock_return.assert_not_called()

    def test_full_pipeline_returned(
        self, mock_voice, mock_formats, mock_fetch_posts, mock_evaluate,
        mock_fetch_brief, mock_save_review, mock_approve, mock_return,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch_posts.return_value = [SYNTHETIC_POST]
        mock_fetch_brief.return_value = SYNTHETIC_BRIEF
        mock_evaluate.return_value = MOCK_EVALUATION_RETURNED
        mock_save_review.return_value = SYNTHETIC_SAVED_REVIEW

        result = agent.run()

        self.assertEqual(len(result), 1)
        mock_return.assert_called_once_with("post-001", 0)
        mock_approve.assert_not_called()

    def test_empty_queue(
        self, mock_voice, mock_formats, mock_fetch_posts, mock_evaluate,
        mock_fetch_brief, mock_save_review, mock_approve, mock_return,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch_posts.return_value = []

        result = agent.run()

        self.assertEqual(result, [])
        mock_evaluate.assert_not_called()

    def test_auto_approve_revision_count_2(
        self, mock_voice, mock_formats, mock_fetch_posts, mock_evaluate,
        mock_fetch_brief, mock_save_review, mock_approve, mock_return,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch_posts.return_value = [SYNTHETIC_POST_REVISION_2]
        mock_save_review.return_value = SYNTHETIC_SAVED_REVIEW

        result = agent.run()

        self.assertEqual(len(result), 1)
        mock_evaluate.assert_not_called()
        mock_fetch_brief.assert_not_called()
        mock_approve.assert_called_once_with("post-002")
        mock_return.assert_not_called()

        # Review saved with revision_notes
        review_arg = mock_save_review.call_args.args[0]
        self.assertEqual(review_arg["decision"], "approved")
        self.assertIsNotNone(review_arg["revision_notes"])
        self.assertIn("2+ revisiones", review_arg["revision_notes"])

    def test_auto_approve_revision_count_3(
        self, mock_voice, mock_formats, mock_fetch_posts, mock_evaluate,
        mock_fetch_brief, mock_save_review, mock_approve, mock_return,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch_posts.return_value = [SYNTHETIC_POST_REVISION_3]
        mock_save_review.return_value = SYNTHETIC_SAVED_REVIEW

        result = agent.run()

        self.assertEqual(len(result), 1)
        mock_evaluate.assert_not_called()
        mock_approve.assert_called_once_with("post-003")

    def test_evaluation_failure_does_not_update_post(
        self, mock_voice, mock_formats, mock_fetch_posts, mock_evaluate,
        mock_fetch_brief, mock_save_review, mock_approve, mock_return,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch_posts.return_value = [SYNTHETIC_POST]
        mock_fetch_brief.return_value = SYNTHETIC_BRIEF
        mock_evaluate.side_effect = ValueError("LLM parse error")

        result = agent.run()

        self.assertEqual(result, [])
        mock_save_review.assert_not_called()
        mock_approve.assert_not_called()
        mock_return.assert_not_called()

    def test_save_review_failure_still_returns_evaluation(
        self, mock_voice, mock_formats, mock_fetch_posts, mock_evaluate,
        mock_fetch_brief, mock_save_review, mock_approve, mock_return,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch_posts.return_value = [SYNTHETIC_POST]
        mock_fetch_brief.return_value = SYNTHETIC_BRIEF
        mock_evaluate.return_value = MOCK_EVALUATION_APPROVED
        mock_save_review.side_effect = Exception("Supabase error")

        result = agent.run()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["decision"], "approved")

    def test_multiple_posts_continues_on_error(
        self, mock_voice, mock_formats, mock_fetch_posts, mock_evaluate,
        mock_fetch_brief, mock_save_review, mock_approve, mock_return,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        post_2 = {**SYNTHETIC_POST, "id": "post-002"}
        mock_fetch_posts.return_value = [SYNTHETIC_POST, post_2]
        mock_fetch_brief.return_value = SYNTHETIC_BRIEF
        mock_evaluate.side_effect = [ValueError("fail"), MOCK_EVALUATION_APPROVED]
        mock_save_review.return_value = SYNTHETIC_SAVED_REVIEW

        result = agent.run()

        self.assertEqual(len(result), 1)
        mock_approve.assert_called_once_with("post-002")

    def test_brief_fetch_failure_still_evaluates(
        self, mock_voice, mock_formats, mock_fetch_posts, mock_evaluate,
        mock_fetch_brief, mock_save_review, mock_approve, mock_return,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch_posts.return_value = [SYNTHETIC_POST]
        mock_fetch_brief.side_effect = Exception("Network error")
        mock_evaluate.return_value = MOCK_EVALUATION_APPROVED
        mock_save_review.return_value = SYNTHETIC_SAVED_REVIEW

        result = agent.run()

        self.assertEqual(len(result), 1)
        mock_evaluate.assert_called_once()
        call_args = mock_evaluate.call_args.args
        self.assertIsNone(call_args[1])

    def test_review_contains_correct_scores(
        self, mock_voice, mock_formats, mock_fetch_posts, mock_evaluate,
        mock_fetch_brief, mock_save_review, mock_approve, mock_return,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        mock_fetch_posts.return_value = [SYNTHETIC_POST]
        mock_fetch_brief.return_value = SYNTHETIC_BRIEF
        mock_evaluate.return_value = MOCK_EVALUATION_APPROVED
        mock_save_review.return_value = SYNTHETIC_SAVED_REVIEW

        agent.run()

        review_arg = mock_save_review.call_args.args[0]
        self.assertEqual(review_arg["post_id"], "post-001")
        self.assertEqual(review_arg["decision"], "approved")
        self.assertEqual(review_arg["overall_score"], 8.25)
        self.assertEqual(review_arg["voice_alignment"], 8.0)
        self.assertEqual(review_arg["factual_rigor"], 7.5)
        self.assertEqual(review_arg["format_compliance"], 9.0)
        self.assertEqual(review_arg["thematic_alignment"], 8.5)
        self.assertEqual(review_arg["summary"], "Buen artículo.")

    def test_returned_post_increments_revision_count(
        self, mock_voice, mock_formats, mock_fetch_posts, mock_evaluate,
        mock_fetch_brief, mock_save_review, mock_approve, mock_return,
    ):
        agent = self._make_agent(mock_voice, mock_formats)
        post_with_1_revision = {**SYNTHETIC_POST, "revision_count": 1}
        mock_fetch_posts.return_value = [post_with_1_revision]
        mock_fetch_brief.return_value = SYNTHETIC_BRIEF
        mock_evaluate.return_value = MOCK_EVALUATION_RETURNED
        mock_save_review.return_value = SYNTHETIC_SAVED_REVIEW

        agent.run()

        mock_return.assert_called_once_with("post-001", 1)


if __name__ == "__main__":
    unittest.main()
