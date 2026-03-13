"""Investiga entidades desconocidas usando Claude Sonnet.

Solo se ejecuta cuando un scout_item tiene needs_research=true.
Produce contexto sobre cada entidad para alimentar el brief.
"""

import json
import logging

from core.agent_config import get_prompt
from core.llm_client import completion
from core.model_config import MODELS

logger = logging.getLogger(__name__)

RESEARCH_PROMPT = get_prompt("analyst", "researcher")


def _extract_json(raw_text: str) -> dict:
    """Extrae JSON del response, manejando markdown fences."""
    text = raw_text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def research_entities(item: dict) -> dict:
    """Investiga entidades desconocidas de un scout_item.

    Args:
        item: scout_item con needs_research=true.

    Returns:
        Dict con research por entidad: {entity_name: {description, category, relevance, key_facts}}
    """
    entities = item.get("entities") or []
    if not entities:
        logger.info("No hay entidades para investigar")
        return {}

    model = MODELS["analyst.researcher"]
    prompt = RESEARCH_PROMPT.format(
        title=item.get("title", ""),
        excerpt=item.get("excerpt", ""),
        source=item.get("source", ""),
        topics=", ".join(item.get("topics", [])),
        entities=", ".join(entities),
        research_reason=item.get("needs_research_reason", ""),
    )

    logger.info(f"Researching {len(entities)} entities with {model}...")
    raw_text = completion(model, [{"role": "user", "content": prompt}], max_tokens=2048)
    research = _extract_json(raw_text)

    logger.info(f"Research complete: {list(research.keys())}")
    return research
