from agents.scout.deduplicator import deduplicate


class TestDeduplicate:
    def test_duplicate_url_filtered(self):
        seen = {"https://example.com/old"}
        items = [
            {"url": "https://example.com/old", "title": "Old"},
            {"url": "https://example.com/new", "title": "New"},
        ]
        result = deduplicate(items, seen)

        assert len(result) == 1
        assert result[0]["title"] == "New"

    def test_new_url_passes(self):
        seen: set[str] = set()
        items = [{"url": "https://example.com/1", "title": "First"}]
        result = deduplicate(items, seen)

        assert len(result) == 1
        assert result[0]["url"] == "https://example.com/1"

    def test_seen_urls_updated(self):
        seen: set[str] = set()
        items = [
            {"url": "https://example.com/a", "title": "A"},
            {"url": "https://example.com/b", "title": "B"},
        ]
        deduplicate(items, seen)

        assert "https://example.com/a" in seen
        assert "https://example.com/b" in seen

    def test_duplicate_within_same_batch(self):
        seen: set[str] = set()
        items = [
            {"url": "https://example.com/same", "title": "First"},
            {"url": "https://example.com/same", "title": "Duplicate"},
        ]
        result = deduplicate(items, seen)

        assert len(result) == 1
        assert result[0]["title"] == "First"

    def test_item_without_url_filtered(self):
        seen: set[str] = set()
        items = [
            {"url": None, "title": "No URL"},
            {"title": "Missing URL key"},
            {"url": "https://example.com/valid", "title": "Valid"},
        ]
        result = deduplicate(items, seen)

        assert len(result) == 1
        assert result[0]["title"] == "Valid"

    def test_empty_list(self):
        seen: set[str] = set()
        result = deduplicate([], seen)
        assert result == []
