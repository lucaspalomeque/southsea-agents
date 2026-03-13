from unittest.mock import patch, MagicMock

from agents.scout.tools.rss_fetcher import fetch_feed, fetch_all_feeds


def _make_feed(entries):
    """Crea un objeto mock de feedparser con entries dados."""
    feed = MagicMock()
    feed.bozo = False
    feed.entries = entries
    return feed


def _make_entry(title="Test Article", link="https://example.com/1",
                summary="This is a test", author="Author",
                published="Wed, 05 Mar 2026 12:00:00 GMT"):
    return {
        "title": title,
        "link": link,
        "summary": summary,
        "author": author,
        "published": published,
        "content": None,
    }


class TestFetchFeed:
    @patch("agents.scout.tools.rss_fetcher.feedparser.parse")
    def test_returns_correct_structure(self, mock_parse):
        mock_parse.return_value = _make_feed([
            _make_entry(
                title="Ethereum hits $5k",
                link="https://coindesk.com/ethereum-5k",
                summary="Ethereum just crossed the $5,000 mark.",
                author="CoinDesk Staff",
            ),
        ])

        items = fetch_feed("https://fake.url/rss", "coindesk", "news")

        assert len(items) == 1
        item = items[0]
        assert item["source"] == "coindesk"
        assert item["source_type"] == "news"
        assert item["url"] == "https://coindesk.com/ethereum-5k"
        assert item["title"] == "Ethereum hits $5k"
        assert item["excerpt"] == "Ethereum just crossed the $5,000 mark."
        assert item["author"] == "CoinDesk Staff"
        assert item["published_at"] is not None
        assert item["collected_at"] is not None

    @patch("agents.scout.tools.rss_fetcher.feedparser.parse")
    def test_empty_feed_returns_empty_list(self, mock_parse):
        mock_parse.return_value = _make_feed([])
        items = fetch_feed("https://fake.url/rss", "bankless", "news")
        assert items == []

    @patch("agents.scout.tools.rss_fetcher.feedparser.parse")
    def test_entry_without_link_is_skipped(self, mock_parse):
        entry = _make_entry()
        del entry["link"]
        # feedparser usa .get("link") que retorna None si no existe
        entry_obj = MagicMock()
        entry_obj.get = lambda k, d=None: entry.get(k, d)
        mock_parse.return_value = _make_feed([entry_obj])

        items = fetch_feed("https://fake.url/rss", "test", "news")
        assert items == []

    @patch("agents.scout.tools.rss_fetcher.feedparser.parse")
    def test_bozo_feed_with_no_entries_returns_empty(self, mock_parse):
        feed = _make_feed([])
        feed.bozo = True
        feed.bozo_exception = Exception("malformed XML")
        mock_parse.return_value = feed

        items = fetch_feed("https://fake.url/rss", "broken", "news")
        assert items == []

    @patch("agents.scout.tools.rss_fetcher.feedparser.parse")
    def test_excerpt_truncated_to_280_chars(self, mock_parse):
        long_summary = "A" * 500
        mock_parse.return_value = _make_feed([
            _make_entry(summary=long_summary),
        ])

        items = fetch_feed("https://fake.url/rss", "test", "news")
        assert len(items[0]["excerpt"]) == 280


class TestFetchAllFeeds:
    @patch("agents.scout.tools.rss_fetcher.fetch_feed")
    def test_aggregates_all_feeds(self, mock_fetch):
        mock_fetch.return_value = [{"title": "item", "url": "https://x.com/1"}]
        items = fetch_all_feeds()
        # 6 feeds configurados, cada uno retorna 1 item
        assert len(items) == 6
        assert mock_fetch.call_count == 6

    @patch("agents.scout.tools.rss_fetcher.fetch_feed")
    def test_continues_on_feed_error(self, mock_fetch):
        mock_fetch.side_effect = [
            Exception("network error"),
            [{"title": "ok", "url": "https://x.com/1"}],
            [{"title": "ok2", "url": "https://x.com/2"}],
            Exception("timeout"),
            [{"title": "ok3", "url": "https://x.com/3"}],
            [{"title": "ok4", "url": "https://x.com/4"}],
        ]
        items = fetch_all_feeds()
        assert len(items) == 4  # 2 feeds fallaron, 4 exitosos
