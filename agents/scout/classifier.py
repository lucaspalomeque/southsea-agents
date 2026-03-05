import json
import logging

import anthropic

from core.config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

CLASSIFY_MODEL = "claude-haiku-4-5-20251001"

VALID_TOPICS = {
    "crypto_defi",
    "crypto_market",
    "web3",
    "ai_tech",
    "genai_art",
    "geopolitics",
    "startups",
    "network_state",
}

CLASSIFY_PROMPT = """Classify each news item into topics and extract named entities.

Valid topics: crypto_defi, crypto_market, web3, ai_tech, genai_art, geopolitics, startups, network_state

Rules:
- Each item can have 1 or more topics, or NONE if it doesn't fit any category
- Only assign topics that are clearly relevant
- Geopolitics only counts if it directly impacts crypto, AI, or tech regulation
- Extract entities: projects, protocols, people, tokens, companies mentioned
- If an item doesn't fit ANY topic, set topics to an empty list

Return a JSON array with one object per item, in the same order as the input:
[
  {
    "index": 0,
    "topics": ["crypto_defi", "crypto_market"],
    "entities": ["Uniswap", "Ethereum"]
  },
  ...
]

Items to classify:
"""


def _build_items_text(items: list[dict]) -> str:
    lines = []
    for i, item in enumerate(items):
        lines.append(
            f"[{i}] title: {item.get('title', '')}\n"
            f"    excerpt: {item.get('excerpt', '')}\n"
            f"    source: {item.get('source', '')}"
        )
    return "\n\n".join(lines)


def _extract_json(raw_text: str) -> list[dict]:
    """Extrae JSON del response, manejando markdown fences."""
    if "```" in raw_text:
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    return json.loads(raw_text)


def classify_items(items: list[dict]) -> list[dict]:
    """Clasifica items usando Claude y descarta los que no encajan en ningun topic."""
    if not items:
        return []

    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY no está definida. Revisá tu archivo .env")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = CLASSIFY_PROMPT + _build_items_text(items)

    logger.info(f"Clasificando {len(items)} items con Claude ({CLASSIFY_MODEL})...")
    response = client.messages.create(
        model=CLASSIFY_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text
    classifications = _extract_json(raw_text)

    classified = []
    discarded = 0
    for cls in classifications:
        idx = cls["index"]
        topics = [t for t in cls.get("topics", []) if t in VALID_TOPICS]
        entities = cls.get("entities", [])

        if not topics:
            discarded += 1
            continue

        item = items[idx].copy()
        item["topics"] = topics
        item["entities"] = entities
        item["needs_research"] = False
        item["needs_research_reason"] = None
        item["status"] = "pending_analysis"
        classified.append(item)

    logger.info(f"Clasificados: {len(classified)}, descartados: {discarded}")
    return classified
