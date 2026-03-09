"""Tests para brief_builder.py — mock de llm_client.completion."""

import unittest
from unittest.mock import patch
import json

from agents.analyst.brief_builder import build_brief, REQUIRED_FIELDS


MOCK_BRIEF_RESPONSE = json.dumps({
    "title": "Hyperliquid y la batalla por el volumen descentralizado",
    "context": "El exchange descentralizado Hyperliquid superó los $1B...\n\nEsto marca un punto de inflexión...",
    "key_entities": [
        {"name": "Hyperliquid", "description": "DEX de perpetuos en L1 propio", "role_in_story": "Protagonista"},
    ],
    "editorial_angle": "La descentralización del trading de derivados avanza más rápido que la regulación. Hyperliquid demuestra que el volumen migra cuando la UX es competitiva.",
    "verified_facts": [
        "Hyperliquid superó $1B en volumen diario",
        "Opera sobre su propia blockchain L1",
    ],
    "research_notes": "Verificar cifra exacta de volumen contra datos on-chain. El claim de 'top 3' necesita contexto temporal.",
})


def _make_item():
    return {
        "id": "item-1",
        "title": "Hyperliquid Surpasses $1B in Daily Volume",
        "excerpt": "The decentralized exchange hit a new milestone...",
        "source": "coindesk",
        "source_type": "news",
        "raw_content": "Full article content here...",
        "topics": ["crypto_defi", "crypto_market"],
        "entities": ["Hyperliquid"],
        "needs_research": False,
    }


def _make_research():
    return {
        "Hyperliquid": {
            "description": "A decentralized perpetual exchange.",
            "category": "protocol",
            "relevance": "Leading DEX by volume.",
            "key_facts": ["Launched own L1", "Top 3 perp DEX"],
        }
    }


class TestBuildBrief(unittest.TestCase):
    @patch("agents.analyst.brief_builder.completion")
    def test_produces_complete_brief(self, mock_completion):
        mock_completion.return_value = MOCK_BRIEF_RESPONSE

        brief = build_brief(_make_item(), _make_research())

        self.assertEqual(brief["scout_item_id"], "item-1")
        self.assertEqual(brief["status"], "pending_writing")
        for field in REQUIRED_FIELDS:
            self.assertIn(field, brief)
        self.assertIsInstance(brief["key_entities"], list)
        self.assertIsInstance(brief["verified_facts"], list)
        self.assertEqual(brief["topics"], ["crypto_defi", "crypto_market"])

    @patch("agents.analyst.brief_builder.completion")
    def test_works_without_research(self, mock_completion):
        mock_completion.return_value = MOCK_BRIEF_RESPONSE

        brief = build_brief(_make_item())
        self.assertEqual(brief["scout_item_id"], "item-1")

    @patch("agents.analyst.brief_builder.completion")
    def test_raises_on_incomplete_brief(self, mock_completion):
        mock_completion.return_value = json.dumps({"title": "Only title"})

        with self.assertRaises(ValueError) as ctx:
            build_brief(_make_item())
        self.assertIn("faltan campos", str(ctx.exception))

    @patch("agents.analyst.brief_builder.completion")
    def test_uses_model_from_config(self, mock_completion):
        mock_completion.return_value = MOCK_BRIEF_RESPONSE

        build_brief(_make_item())

        call_args = mock_completion.call_args
        self.assertIn("sonnet", call_args[0][0])


if __name__ == "__main__":
    unittest.main()
