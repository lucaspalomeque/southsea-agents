"""Construye briefs estructurados para el Writer Agent.

Toma un scout_item + research opcional y produce un brief con:
title, context, key_entities, editorial_angle, verified_facts, research_notes.
"""

import json
import logging

from core.agent_config import get_prompt
from core.llm_client import completion
from core.model_config import MODELS

logger = logging.getLogger(__name__)

BRIEF_PROMPT = get_prompt("analyst", "brief_builder")


def _extract_json(raw_text: str) -> dict:
    """Extrae JSON del response, manejando markdown fences."""
    text = raw_text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def _format_research_section(research: dict) -> str:
    """Formatea research results para incluir en el prompt."""
    if not research:
        return "RESEARCH: No additional research was performed for this item."

    lines = ["RESEARCH ON ENTITIES:"]
    for name, info in research.items():
        lines.append(f"\n{name}:")
        lines.append(f"  Description: {info.get('description', 'N/A')}")
        lines.append(f"  Category: {info.get('category', 'N/A')}")
        lines.append(f"  Relevance: {info.get('relevance', 'N/A')}")
        facts = info.get("key_facts", [])
        if facts:
            lines.append(f"  Key facts: {'; '.join(facts)}")
    return "\n".join(lines)


REQUIRED_FIELDS = {"title", "context", "key_entities", "editorial_angle", "verified_facts", "research_notes"}


def build_brief(item: dict, research: dict | None = None) -> dict:
    """Construye un brief estructurado para el Writer.

    Args:
        item: scout_item dict.
        research: Research results from researcher.py (optional).

    Returns:
        Dict con campos de analyst_briefs listo para guardar en Supabase.
    """
    model = MODELS["analyst.brief_builder"]
    research_section = _format_research_section(research or {})

    prompt = BRIEF_PROMPT.format(
        title=item.get("title", ""),
        source=item.get("source", ""),
        source_type=item.get("source_type", ""),
        excerpt=item.get("excerpt", ""),
        raw_content=(item.get("raw_content") or "")[:3000] or "Not available",
        topics=", ".join(item.get("topics", [])),
        entities=", ".join(item.get("entities", []) or []),
        research_section=research_section,
    )

    logger.info(f"Building brief for: {item.get('title', '?')}")
    raw_text = completion(model, [{"role": "user", "content": prompt}], max_tokens=2048)
    brief_data = _extract_json(raw_text)

    missing = REQUIRED_FIELDS - set(brief_data.keys())
    if missing:
        raise ValueError(f"Brief incompleto, faltan campos: {missing}")

    return {
        "scout_item_id": item["id"],
        "title": brief_data["title"],
        "context": brief_data["context"],
        "key_entities": brief_data["key_entities"],
        "editorial_angle": brief_data["editorial_angle"],
        "verified_facts": brief_data["verified_facts"],
        "research_notes": brief_data["research_notes"],
        "topics": item.get("topics", []),
        "status": "pending_writing",
    }
