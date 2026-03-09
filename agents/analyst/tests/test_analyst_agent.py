"""Tests para analyst_agent.py — mock completo del pipeline."""

import unittest
from unittest.mock import patch, MagicMock, call

from agents.analyst.analyst_agent import AnalystAgent


def _make_item(item_id="item-1", needs_research=False):
    return {
        "id": item_id,
        "title": "Test Item",
        "excerpt": "Test excerpt",
        "source": "coindesk",
        "source_type": "news",
        "raw_content": "Full content",
        "topics": ["crypto_defi"],
        "entities": ["Ethereum"],
        "needs_research": needs_research,
        "needs_research_reason": "Entidad desconocida: X" if needs_research else None,
        "status": "pending_analysis",
    }


MOCK_BRIEF = {
    "scout_item_id": "item-1",
    "title": "Brief Title",
    "context": "Context",
    "key_entities": [],
    "editorial_angle": "Angle",
    "verified_facts": ["fact1"],
    "research_notes": "",
    "topics": ["crypto_defi"],
    "status": "pending_writing",
}


@patch("agents.analyst.analyst_agent.save_brief")
@patch("agents.analyst.analyst_agent.build_brief")
@patch("agents.analyst.analyst_agent.research_entities")
@patch("agents.analyst.analyst_agent.update_scout_item")
@patch("agents.analyst.analyst_agent.fetch_pending_items")
class TestAnalystAgent(unittest.TestCase):
    def test_full_pipeline_no_research(self, mock_fetch, mock_update, mock_research, mock_build, mock_save):
        mock_fetch.return_value = [_make_item()]
        mock_build.return_value = MOCK_BRIEF
        mock_save.return_value = MOCK_BRIEF

        agent = AnalystAgent()
        result = agent.run()

        self.assertEqual(len(result), 1)
        mock_research.assert_not_called()
        mock_build.assert_called_once()
        mock_save.assert_called_once_with(MOCK_BRIEF)

        update_calls = mock_update.call_args_list
        self.assertEqual(update_calls[0], call("item-1", {"status": "in_analysis"}))
        self.assertEqual(update_calls[1], call("item-1", {"status": "processed"}))

    def test_full_pipeline_with_research(self, mock_fetch, mock_update, mock_research, mock_build, mock_save):
        mock_fetch.return_value = [_make_item(needs_research=True)]
        mock_research.return_value = {"Ethereum": {"description": "Smart contract platform"}}
        mock_build.return_value = MOCK_BRIEF
        mock_save.return_value = MOCK_BRIEF

        agent = AnalystAgent()
        result = agent.run()

        self.assertEqual(len(result), 1)
        mock_research.assert_called_once()
        mock_build.assert_called_once()
        research_arg = mock_build.call_args.args[1]
        self.assertIn("Ethereum", research_arg)

    def test_empty_queue(self, mock_fetch, mock_update, mock_research, mock_build, mock_save):
        mock_fetch.return_value = []

        agent = AnalystAgent()
        result = agent.run()

        self.assertEqual(result, [])
        mock_update.assert_not_called()
        mock_build.assert_not_called()

    def test_error_rolls_back_status(self, mock_fetch, mock_update, mock_research, mock_build, mock_save):
        mock_fetch.return_value = [_make_item()]
        mock_build.side_effect = ValueError("Claude returned garbage")

        agent = AnalystAgent()
        result = agent.run()

        self.assertEqual(result, [])
        # First call: in_analysis, second call: rollback to pending_analysis
        update_calls = mock_update.call_args_list
        self.assertEqual(update_calls[0], call("item-1", {"status": "in_analysis"}))
        self.assertEqual(update_calls[1], call("item-1", {"status": "pending_analysis"}))

    def test_multiple_items_continues_on_error(self, mock_fetch, mock_update, mock_research, mock_build, mock_save):
        mock_fetch.return_value = [_make_item("item-1"), _make_item("item-2")]
        mock_build.side_effect = [ValueError("fail"), MOCK_BRIEF]
        mock_save.return_value = MOCK_BRIEF

        agent = AnalystAgent()
        result = agent.run()

        # item-1 fails, item-2 succeeds
        self.assertEqual(len(result), 1)

    def test_batch_size_passed_to_fetch(self, mock_fetch, mock_update, mock_research, mock_build, mock_save):
        mock_fetch.return_value = []

        agent = AnalystAgent(batch_size=5)
        agent.run()

        mock_fetch.assert_called_once_with(limit=5)


if __name__ == "__main__":
    unittest.main()
