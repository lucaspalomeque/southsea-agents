import json
import logging

from core.agent_config import get_prompt
from core.llm_client import completion
from core.model_config import MODELS

logger = logging.getLogger(__name__)

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

CLASSIFY_PROMPT = get_prompt("scout", "classifier")


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

    model = MODELS["scout.classifier"]
    prompt = CLASSIFY_PROMPT + _build_items_text(items)

    logger.info(f"Clasificando {len(items)} items con {model}...")
    raw_text = completion(model, [{"role": "user", "content": prompt}], max_tokens=4096)
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
