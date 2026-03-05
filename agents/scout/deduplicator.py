import logging

logger = logging.getLogger(__name__)


def deduplicate(items: list[dict], seen_urls: set[str]) -> list[dict]:
    """Filtra items cuya URL ya fue vista. Actualiza seen_urls in-place."""
    unique = []
    duplicates = 0

    for item in items:
        url = item.get("url")
        if not url or url in seen_urls:
            duplicates += 1
            continue
        seen_urls.add(url)
        unique.append(item)

    if duplicates:
        logger.info(f"Deduplicados: {duplicates} items removidos")
    return unique
