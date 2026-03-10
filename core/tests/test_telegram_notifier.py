"""Tests para core/telegram_notifier.py."""

import unittest
from unittest.mock import MagicMock, patch

import httpx


class TestSendReport(unittest.TestCase):
    """Tests para send_report."""

    @patch("core.telegram_notifier.SOUTHSEA_CHAT_ID", "123456")
    @patch("core.telegram_notifier.SOUTHSEA_BOT_TOKEN", "fake-token")
    @patch("core.telegram_notifier.httpx.post")
    def test_send_report_success(self, mock_post):
        from core.telegram_notifier import send_report

        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()

        result = send_report("Pipeline OK")

        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch("core.telegram_notifier.SOUTHSEA_CHAT_ID", "123456")
    @patch("core.telegram_notifier.SOUTHSEA_BOT_TOKEN", "fake-token")
    @patch("core.telegram_notifier.httpx.post")
    def test_send_report_http_error(self, mock_post):
        from core.telegram_notifier import send_report

        mock_post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 Forbidden", request=MagicMock(), response=MagicMock()
        )

        result = send_report("Pipeline OK")

        self.assertFalse(result)

    @patch("core.telegram_notifier.SOUTHSEA_CHAT_ID", "123456")
    @patch("core.telegram_notifier.SOUTHSEA_BOT_TOKEN", None)
    @patch("core.telegram_notifier.httpx.post")
    def test_send_report_missing_token(self, mock_post):
        from core.telegram_notifier import send_report

        result = send_report("Pipeline OK")

        self.assertFalse(result)
        mock_post.assert_not_called()

    @patch("core.telegram_notifier.SOUTHSEA_CHAT_ID", None)
    @patch("core.telegram_notifier.SOUTHSEA_BOT_TOKEN", "fake-token")
    @patch("core.telegram_notifier.httpx.post")
    def test_send_report_missing_chat_id(self, mock_post):
        from core.telegram_notifier import send_report

        result = send_report("Pipeline OK")

        self.assertFalse(result)
        mock_post.assert_not_called()

    @patch("core.telegram_notifier.SOUTHSEA_CHAT_ID", "123456")
    @patch("core.telegram_notifier.SOUTHSEA_BOT_TOKEN", "fake-token")
    @patch("core.telegram_notifier.httpx.post")
    def test_send_report_correct_payload(self, mock_post):
        from core.telegram_notifier import send_report

        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()

        send_report("Test report text")

        call_args = mock_post.call_args
        self.assertEqual(
            call_args.args[0],
            "https://api.telegram.org/botfake-token/sendMessage",
        )
        self.assertEqual(call_args.kwargs["json"]["chat_id"], "123456")
        self.assertEqual(call_args.kwargs["json"]["text"], "Test report text")


if __name__ == "__main__":
    unittest.main()
