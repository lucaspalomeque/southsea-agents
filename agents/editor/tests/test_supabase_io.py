"""Tests para supabase_io.py del Editor — mock de httpx."""

import unittest
from unittest.mock import patch, MagicMock

from agents.editor.supabase_io import (
    fetch_pending_posts,
    fetch_brief,
    save_review,
    approve_post,
    return_post,
)


def _mock_response(json_data, status_code=200):
    mock = MagicMock()
    mock.json.return_value = json_data
    mock.status_code = status_code
    mock.raise_for_status = MagicMock()
    return mock


@patch("agents.editor.supabase_io.httpx.post")
class TestFetchPendingPosts(unittest.TestCase):
    def test_fetches_posts_with_pending_editing(self, mock_post):
        mock_post.return_value = _mock_response({"data": [{"id": "p1"}, {"id": "p2"}]})

        result = fetch_pending_posts(limit=5)

        self.assertEqual(len(result), 2)
        call_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(call_json["table"], "posts")
        self.assertEqual(call_json["filters"]["status"], "pending_review")
        self.assertEqual(call_json["limit"], 5)

    def test_returns_empty_on_no_data(self, mock_post):
        mock_post.return_value = _mock_response({"data": []})

        result = fetch_pending_posts()

        self.assertEqual(result, [])


@patch("agents.editor.supabase_io.httpx.post")
class TestFetchBrief(unittest.TestCase):
    def test_fetches_brief_by_id(self, mock_post):
        mock_post.return_value = _mock_response({"data": [{"id": "b1", "title": "Test"}]})

        result = fetch_brief("b1")

        self.assertEqual(result["id"], "b1")
        call_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(call_json["table"], "analyst_briefs")
        self.assertEqual(call_json["filters"]["id"], "b1")

    def test_returns_none_if_not_found(self, mock_post):
        mock_post.return_value = _mock_response({"data": []})

        result = fetch_brief("nonexistent")

        self.assertIsNone(result)


@patch("agents.editor.supabase_io.httpx.post")
class TestSaveReview(unittest.TestCase):
    def test_saves_review_with_all_fields(self, mock_post):
        mock_post.return_value = _mock_response({"data": {"id": "r1"}})

        review = {
            "post_id": "post-001",
            "decision": "approved",
            "voice_alignment": 8.0,
            "factual_rigor": 7.5,
            "format_compliance": 9.0,
            "thematic_alignment": 8.5,
            "overall_score": 8.25,
            "summary": "Buen artículo.",
            "revision_notes": None,
        }
        result = save_review(review)

        self.assertEqual(result, {"id": "r1"})
        call_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(call_json["table"], "editor_reviews")
        self.assertEqual(call_json["post_id"], "post-001")
        self.assertEqual(call_json["decision"], "approved")
        self.assertEqual(call_json["voice_alignment"], 8.0)
        self.assertEqual(call_json["overall_score"], 8.25)
        # None values stripped
        self.assertNotIn("revision_notes", call_json)


@patch("agents.editor.supabase_io.httpx.post")
class TestApprovePost(unittest.TestCase):
    def test_marks_editor_approved(self, mock_post):
        mock_post.return_value = _mock_response({"data": {"id": "p1", "editor_approved": True}})

        result = approve_post("p1")

        call_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(call_json["table"], "posts")
        self.assertEqual(call_json["id"], "p1")
        self.assertTrue(call_json["updates"]["editor_approved"])


@patch("agents.editor.supabase_io.httpx.post")
class TestReturnPost(unittest.TestCase):
    def test_updates_to_draft_with_revision_count(self, mock_post):
        mock_post.return_value = _mock_response({"data": {"id": "p1", "status": "draft"}})

        result = return_post("p1", revision_count=0)

        call_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(call_json["table"], "posts")
        self.assertEqual(call_json["id"], "p1")
        self.assertEqual(call_json["updates"]["status"], "draft")
        self.assertEqual(call_json["updates"]["revision_count"], 1)


if __name__ == "__main__":
    unittest.main()
