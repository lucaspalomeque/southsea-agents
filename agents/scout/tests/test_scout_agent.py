"""Tests para ScoutAgent (agents/scout/scout_agent.py)."""

import unittest
from unittest.mock import MagicMock, patch


class TestScoutAgentBatchSize(unittest.TestCase):
    """Tests para batch_size en ScoutAgent."""

    @patch("agents.scout.scout_agent.ingest_item")
    @patch("agents.scout.scout_agent.deduplicate")
    @patch("agents.scout.scout_agent.classify_items")
    @patch("agents.scout.scout_agent.fetch_all_feeds")
    def test_batch_size_limits_ingested_items(
        self, mock_fetch, mock_classify, mock_dedup, mock_ingest
    ):
        from agents.scout.scout_agent import ScoutAgent

        items = [{"title": f"Item {i}", "url": f"http://x.com/{i}"} for i in range(5)]
        mock_fetch.return_value = items
        mock_classify.return_value = items
        mock_dedup.return_value = items
        mock_ingest.side_effect = lambda item: item

        agent = ScoutAgent(batch_size=1)
        result = agent.run()

        self.assertEqual(len(result), 1)
        self.assertEqual(mock_ingest.call_count, 1)

    @patch("agents.scout.scout_agent.ingest_item")
    @patch("agents.scout.scout_agent.deduplicate")
    @patch("agents.scout.scout_agent.classify_items")
    @patch("agents.scout.scout_agent.fetch_all_feeds")
    def test_no_batch_size_processes_all(
        self, mock_fetch, mock_classify, mock_dedup, mock_ingest
    ):
        from agents.scout.scout_agent import ScoutAgent

        items = [{"title": f"Item {i}", "url": f"http://x.com/{i}"} for i in range(5)]
        mock_fetch.return_value = items
        mock_classify.return_value = items
        mock_dedup.return_value = items
        mock_ingest.side_effect = lambda item: item

        agent = ScoutAgent()
        result = agent.run()

        self.assertEqual(len(result), 5)
        self.assertEqual(mock_ingest.call_count, 5)


if __name__ == "__main__":
    unittest.main()
