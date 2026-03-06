import json
from unittest.mock import patch, MagicMock

from agents.scout.classifier import classify_items, VALID_TOPICS


def _make_item(title, excerpt="", source="test"):
    return {
        "source": source,
        "source_type": "news",
        "url": f"https://example.com/{title.replace(' ', '-')}",
        "title": title,
        "excerpt": excerpt,
        "collected_at": "2026-03-05T00:00:00+00:00",
    }


class TestClassifier:
    @patch("agents.scout.classifier.completion")
    def test_ethereum_defi_classified_correctly(self, mock_completion):
        mock_completion.return_value = json.dumps([
            {"index": 0, "topics": ["crypto_defi"], "entities": ["Ethereum", "Uniswap"]},
        ])

        items = [_make_item("Uniswap v4 launches on Ethereum", "New AMM features...")]
        result = classify_items(items)

        assert len(result) == 1
        assert "crypto_defi" in result[0]["topics"]
        assert "Ethereum" in result[0]["entities"]
        assert result[0]["status"] == "pending_analysis"
        assert result[0]["needs_research"] is False

    @patch("agents.scout.classifier.completion")
    def test_irrelevant_item_discarded(self, mock_completion):
        mock_completion.return_value = json.dumps([
            {"index": 0, "topics": [], "entities": []},
        ])

        items = [_make_item("Local weather update for Tuesday")]
        result = classify_items(items)

        assert len(result) == 0

    @patch("agents.scout.classifier.completion")
    def test_genai_art_classified(self, mock_completion):
        mock_completion.return_value = json.dumps([
            {"index": 0, "topics": ["genai_art", "ai_tech"], "entities": ["Midjourney", "Stable Diffusion"]},
        ])

        items = [_make_item("Midjourney v7 changes the game for AI art")]
        result = classify_items(items)

        assert len(result) == 1
        assert "genai_art" in result[0]["topics"]
        assert "ai_tech" in result[0]["topics"]

    @patch("agents.scout.classifier.completion")
    def test_mixed_batch_filters_correctly(self, mock_completion):
        mock_completion.return_value = json.dumps([
            {"index": 0, "topics": ["crypto_market"], "entities": ["Bitcoin"]},
            {"index": 1, "topics": [], "entities": []},
            {"index": 2, "topics": ["startups", "ai_tech"], "entities": ["Anthropic"]},
        ])

        items = [
            _make_item("Bitcoin breaks $100k"),
            _make_item("Celebrity gossip roundup"),
            _make_item("Anthropic raises $5B Series D"),
        ]
        result = classify_items(items)

        assert len(result) == 2
        assert result[0]["title"] == "Bitcoin breaks $100k"
        assert result[1]["title"] == "Anthropic raises $5B Series D"

    @patch("agents.scout.classifier.completion")
    def test_invalid_topics_filtered_out(self, mock_completion):
        mock_completion.return_value = json.dumps([
            {"index": 0, "topics": ["crypto_defi", "invalid_topic"], "entities": []},
        ])

        items = [_make_item("DeFi protocol update")]
        result = classify_items(items)

        assert len(result) == 1
        assert result[0]["topics"] == ["crypto_defi"]
        assert "invalid_topic" not in result[0]["topics"]

    def test_empty_input_returns_empty(self):
        result = classify_items([])
        assert result == []

    @patch("agents.scout.classifier.completion")
    def test_response_with_markdown_fences(self, mock_completion):
        classifications = [{"index": 0, "topics": ["web3"], "entities": ["IPFS"]}]
        mock_completion.return_value = f"```json\n{json.dumps(classifications)}\n```"

        items = [_make_item("IPFS adoption grows")]
        result = classify_items(items)

        assert len(result) == 1
        assert "web3" in result[0]["topics"]
