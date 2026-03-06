"""Tests para llm_client.py — parsing de providers y dispatch."""

import unittest
from unittest.mock import patch, MagicMock

from core.llm_client import completion, _parse_provider


class TestParseProvider(unittest.TestCase):
    def test_anthropic_prefix(self):
        provider, model_id = _parse_provider("anthropic/claude-haiku-4-5-20251001")
        assert provider == "anthropic"
        assert model_id == "claude-haiku-4-5-20251001"

    def test_openrouter_prefix(self):
        provider, model_id = _parse_provider("openrouter/google/gemini-2.0-flash")
        assert provider == "openrouter"
        assert model_id == "google/gemini-2.0-flash"

    def test_no_prefix_defaults_to_anthropic(self):
        provider, model_id = _parse_provider("claude-sonnet-4-20250514")
        assert provider == "anthropic"
        assert model_id == "claude-sonnet-4-20250514"


class TestCompletionAnthropic(unittest.TestCase):
    @patch("core.llm_client.ANTHROPIC_API_KEY", "sk-test")
    @patch("core.llm_client.anthropic.Anthropic")
    def test_calls_anthropic_correctly(self, mock_cls):
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="response text")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_msg
        mock_cls.return_value = mock_client

        result = completion("anthropic/claude-haiku-4-5-20251001", [{"role": "user", "content": "hi"}], max_tokens=100)

        assert result == "response text"
        mock_client.messages.create.assert_called_once_with(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{"role": "user", "content": "hi"}],
        )

    @patch("core.llm_client.ANTHROPIC_API_KEY", None)
    def test_raises_without_api_key(self):
        with self.assertRaises(RuntimeError) as ctx:
            completion("anthropic/claude-haiku-4-5-20251001", [{"role": "user", "content": "hi"}])
        assert "ANTHROPIC_API_KEY" in str(ctx.exception)


class TestCompletionOpenRouter(unittest.TestCase):
    @patch("core.llm_client.OPENROUTER_API_KEY", "or-test")
    @patch("core.llm_client.httpx.post")
    def test_calls_openrouter_correctly(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "or response"}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = completion("openrouter/google/gemini-2.0-flash", [{"role": "user", "content": "hi"}], max_tokens=200)

        assert result == "or response"
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["json"]["model"] == "google/gemini-2.0-flash"

    @patch("core.llm_client.OPENROUTER_API_KEY", None)
    def test_raises_without_api_key(self):
        with self.assertRaises(RuntimeError) as ctx:
            completion("openrouter/google/gemini-2.0-flash", [{"role": "user", "content": "hi"}])
        assert "OPENROUTER_API_KEY" in str(ctx.exception)


class TestUnknownProvider(unittest.TestCase):
    def test_raises_on_unknown(self):
        with self.assertRaises(ValueError) as ctx:
            _parse_provider("unknown/some-model")
        assert "desconocido" in str(ctx.exception)


if __name__ == "__main__":
    unittest.main()
