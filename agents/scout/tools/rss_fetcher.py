import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    {
        "url": "https://coindesk.com/arc/outboundfeeds/rss/",
        "source": "coindesk",
        "source_type": "news",
    },
    {
        "url": "https://banklesshq.com/feed",
        "source": "bankless",
        "source_type": "news",
    },
    {
        "url": "https://coinbureau.com/feed",
        "source": "coin_bureau",
        "source_type": "news",
    },
    {
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCGqMDsB2HtMOhxX3elYB7rg",
        "source": "yt_network_state",
        "source_type": "video",
    },
    {
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC9-y-6csu5WGm29I7JiwpnA",
        "source": "yt_a16z",
        "source_type": "video",
    },
    {
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCcefcZRL2oaA_uBNeo5UOWg",
        "source": "yt_ycombinator",
        "source_type": "video",
    },
]


def _parse_date(entry: dict) -> str | None:
    for field in ("published", "updated"):
        raw = entry.get(field)
        if not raw:
            continue
        try:
            dt = parsedate_to_datetime(raw)
            return dt.isoformat()
        except Exception:
            pass
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.isoformat()
        except Exception:
            pass
    return None


def _extract_excerpt(entry: dict) -> str:
    summary = entry.get("summary") or entry.get("description") or ""
    return summary[:280]


def fetch_feed(url: str, source: str, source_type: str) -> list[dict]:
    """Parsea un feed RSS y retorna items con la estructura de scout_items."""
    logger.info(f"Fetching feed: {source} ({url})")
    feed = feedparser.parse(url)

    if feed.bozo and not feed.entries:
        logger.warning(f"Feed {source} falló: {feed.bozo_exception}")
        return []

    items = []
    now = datetime.now(timezone.utc).isoformat()

    for entry in feed.entries:
        link = entry.get("link")
        if not link:
            continue

        items.append({
            "source": source,
            "source_type": source_type,
            "url": link,
            "title": entry.get("title", ""),
            "excerpt": _extract_excerpt(entry),
            "raw_content": entry.get("content", [{}])[0].get("value") if entry.get("content") else None,
            "author": entry.get("author"),
            "published_at": _parse_date(entry),
            "collected_at": now,
        })

    logger.info(f"  {source}: {len(items)} items obtenidos")
    return items


def fetch_all_feeds() -> list[dict]:
    """Fetch de todos los feeds RSS configurados."""
    all_items = []
    for feed_config in RSS_FEEDS:
        try:
            items = fetch_feed(
                url=feed_config["url"],
                source=feed_config["source"],
                source_type=feed_config["source_type"],
            )
            all_items.extend(items)
        except Exception as e:
            logger.error(f"Error en feed {feed_config['source']}: {e}")
            continue
    return all_items
