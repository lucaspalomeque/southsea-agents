"""Tests para supabase_io.py — mock de httpx."""

import unittest
from unittest.mock import patch, MagicMock

from agents.writer.supabase_io import fetch_pending_briefs, save_post, update_brief_status


def _mock_response(json_data, status_code=200):
    mock = MagicMock()
    mock.json.return_value = json_data
    mock.status_code = status_code
    mock.raise_for_status = MagicMock()
    return mock


@patch("agents.writer.supabase_io.httpx.post")
class TestFetchPendingBriefs(unittest.TestCase):
    def test_fetches_briefs(self, mock_post):
        mock_post.return_value = _mock_response({"data": [{"id": "b1"}, {"id": "b2"}]})

        result = fetch_pending_briefs(limit=5)

        self.assertEqual(len(result), 2)
        call_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(call_json["table"], "analyst_briefs")
        self.assertEqual(call_json["filters"]["status"], "pending_writing")
        self.assertEqual(call_json["limit"], 5)

    def test_returns_empty_on_no_data(self, mock_post):
        mock_post.return_value = _mock_response({"data": []})

        result = fetch_pending_briefs()

        self.assertEqual(result, [])


@patch("agents.writer.supabase_io.httpx.post")
class TestSavePost(unittest.TestCase):
    def test_saves_post_with_all_fields(self, mock_post):
        mock_post.return_value = _mock_response({"data": {"id": "post-1"}})

        post = {
            "title": "Test",
            "content": "Content",
            "excerpt": "Excerpt",
            "tags": ["crypto"],
            "content_format": "analysis",
            "status": "pending_review",
            "created_by": "writer-agent",
            "original_language": "es",
            "analyst_brief_id": "brief-1",
        }
        result = save_post(post)

        self.assertEqual(result, {"id": "post-1"})
        call_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(call_json["table"], "posts")
        self.assertEqual(call_json["title"], "Test")
        self.assertEqual(call_json["status"], "pending_review")
        self.assertEqual(call_json["content_format"], "analysis")


@patch("agents.writer.supabase_io.httpx.post")
class TestUpdateBriefStatus(unittest.TestCase):
    def test_updates_status(self, mock_post):
        mock_post.return_value = _mock_response({"data": {"id": "b1", "status": "processed"}})

        result = update_brief_status("b1", "processed")

        call_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(call_json["table"], "analyst_briefs")
        self.assertEqual(call_json["id"], "b1")
        self.assertEqual(call_json["updates"]["status"], "processed")


if __name__ == "__main__":
    unittest.main()
