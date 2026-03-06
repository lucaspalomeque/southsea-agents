"""Tests para supabase_io.py — mock de httpx, sin llamadas reales."""

import unittest
from unittest.mock import patch, MagicMock

from agents.analyst.supabase_io import fetch_pending_items, update_scout_item, save_brief


def _mock_response(data, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    return resp


class TestFetchPendingItems(unittest.TestCase):
    @patch("agents.analyst.supabase_io.httpx.post")
    def test_returns_items(self, mock_post):
        mock_post.return_value = _mock_response({
            "success": True,
            "data": [{"id": "abc", "title": "Test", "status": "pending_analysis"}],
            "count": 1,
        })
        items = fetch_pending_items(limit=5)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "abc")

        call_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(call_json["table"], "scout_items")
        self.assertEqual(call_json["filters"]["status"], "pending_analysis")
        self.assertEqual(call_json["limit"], 5)

    @patch("agents.analyst.supabase_io.httpx.post")
    def test_returns_empty_when_no_items(self, mock_post):
        mock_post.return_value = _mock_response({"success": True, "data": [], "count": 0})
        items = fetch_pending_items()
        self.assertEqual(items, [])


class TestUpdateScoutItem(unittest.TestCase):
    @patch("agents.analyst.supabase_io.httpx.post")
    def test_sends_correct_payload(self, mock_post):
        mock_post.return_value = _mock_response({
            "success": True,
            "data": {"id": "abc", "status": "in_analysis"},
        })
        result = update_scout_item("abc", {"status": "in_analysis"})
        self.assertEqual(result["status"], "in_analysis")

        call_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(call_json["table"], "scout_items")
        self.assertEqual(call_json["id"], "abc")
        self.assertEqual(call_json["updates"]["status"], "in_analysis")


class TestSaveBrief(unittest.TestCase):
    @patch("agents.analyst.supabase_io.httpx.post")
    def test_sends_correct_payload(self, mock_post):
        mock_post.return_value = _mock_response({
            "success": True,
            "data": {"id": "brief-1", "scout_item_id": "abc"},
        })
        brief = {
            "scout_item_id": "abc",
            "title": "Test Brief",
            "context": "Some context",
            "key_entities": [],
            "editorial_angle": "An angle",
            "verified_facts": ["fact1"],
            "research_notes": "",
            "status": "pending_writing",
        }
        result = save_brief(brief)
        self.assertEqual(result["scout_item_id"], "abc")

        call_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(call_json["table"], "analyst_briefs")
        self.assertEqual(call_json["record"]["scout_item_id"], "abc")


if __name__ == "__main__":
    unittest.main()
