"""Construye briefs estructurados para el Writer Agent.

Toma un scout_item + research opcional y produce un brief con:
title, context, key_entities, editorial_angle, verified_facts, research_notes.
"""

import json
import logging

from core.llm_client import completion
from core.model_config import MODELS

logger = logging.getLogger(__name__)

BRIEF_PROMPT = """You are the Analyst for The Southmetaverse Sea, a crypto/AI editorial.

Your job: transform a raw news item into a structured brief that a Writer agent will use to create an article.

Editorial voice references (the Writer will apply these, but you should set the angle):
- Techno-optimist: the future crypto+AI are building is better than the present
- Harari-style: connect micro events to macro narratives
- d/acc: technology that empowers individuals, skepticism toward centralized control
- Network State: networks replace states, sovereignty through code

NEWS ITEM:
Title: {title}
Source: {source} ({source_type})
Excerpt: {excerpt}
Raw content: {raw_content}
Topics: {topics}
Entities: {entities}

{research_section}

Produce a JSON object with these fields:

{{
  "title": "A compelling editorial title in the language of the original content (not a copy of the source title)",
  "context": "2-3 paragraphs explaining the news, its background, and why it matters. In the same language as the original content.",
  "key_entities": [
    {{"name": "EntityName", "description": "What it is", "role_in_story": "Why it matters here"}}
  ],
  "editorial_angle": "1-2 sentences describing the specific angle the Writer should take. What's the thesis? What perspective makes this uniquely Southmetaverse Sea?",
  "verified_facts": ["fact 1 that can be stated with confidence", "fact 2", "..."],
  "research_notes": "Any caveats, unverified claims, things the Writer should be careful about, or additional context."
}}

RULES:
- verified_facts must be statements you are confident are true based on the provided information
- If something is uncertain, put it in research_notes, NOT in verified_facts
- editorial_angle should be opinionated — this is not neutral journalism
- context should give the Writer enough background to write without additional research
- Maintain the original language of the content (Spanish stays Spanish, English stays English)
"""


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
        "status": "pending_writing",
    }
