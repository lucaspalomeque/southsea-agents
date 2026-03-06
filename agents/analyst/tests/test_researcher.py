"""Tests para researcher.py — mock de llm_client.completion."""

import unittest
from unittest.mock import patch
import json

from agents.analyst.researcher import research_entities


MOCK_RESEARCH_RESPONSE = json.dumps({
    "Hyperliquid": {
        "description": "A decentralized perpetual exchange on its own L1 chain.",
        "category": "protocol",
        "relevance": "Leading DEX by volume, challenging centralized exchanges.",
        "key_facts": [
            "Launched its own L1 blockchain",
            "Top 3 perp DEX by daily volume",
        ],
    }
})


def _make_item(needs_research=True):
    return {
        "id": "item-1",
        "title": "Hyperliquid Surpasses $1B in Daily Volume",
        "excerpt": "The decentralized exchange hit a new milestone...",
        "source": "coindesk",
        "topics": ["crypto_defi"],
        "entities": ["Hyperliquid"],
        "needs_research": needs_research,
        "needs_research_reason": "Entidad desconocida: Hyperliquid" if needs_research else None,
    }


class TestResearchEntities(unittest.TestCase):
    @patch("agents.analyst.researcher.completion")
    def test_returns_research_for_entities(self, mock_completion):
        mock_completion.return_value = MOCK_RESEARCH_RESPONSE

        result = research_entities(_make_item())

        self.assertIn("Hyperliquid", result)
        self.assertEqual(result["Hyperliquid"]["category"], "protocol")
        self.assertIsInstance(result["Hyperliquid"]["key_facts"], list)

        call_args = mock_completion.call_args
        self.assertIn("sonnet", call_args[0][0])

    @patch("agents.analyst.researcher.completion")
    def test_returns_empty_when_no_entities(self, mock_completion):
        item = _make_item()
        item["entities"] = []
        result = research_entities(item)
        self.assertEqual(result, {})
        mock_completion.assert_not_called()

    @patch("agents.analyst.researcher.completion")
    def test_handles_markdown_fenced_json(self, mock_completion):
        mock_completion.return_value = f"```json\n{MOCK_RESEARCH_RESPONSE}\n```"

        result = research_entities(_make_item())
        self.assertIn("Hyperliquid", result)


if __name__ == "__main__":
    unittest.main()
