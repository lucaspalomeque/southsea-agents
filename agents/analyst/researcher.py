"""Investiga entidades desconocidas usando Claude Sonnet.

Solo se ejecuta cuando un scout_item tiene needs_research=true.
Produce contexto sobre cada entidad para alimentar el brief.
"""

import json
import logging

import anthropic

from core.config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

RESEARCH_MODEL = "claude-sonnet-4-20250514"

RESEARCH_PROMPT = """You are a research analyst for a crypto/AI editorial team.

Given a news item and a list of entities that need research, provide factual context about each entity.

For each entity, return:
- description: What is it? (1-2 sentences)
- category: One of: protocol, token, person, company, dao, chain, tool, other
- relevance: Why does it matter in the crypto/AI space? (1 sentence)
- key_facts: List of 2-4 verified factual statements

IMPORTANT:
- Only state facts you are confident about. If unsure, say "unverified" explicitly.
- Do not speculate or invent information.
- Focus on what's relevant to crypto, DeFi, AI, and Web3.

News item:
Title: {title}
Excerpt: {excerpt}
Source: {source}
Topics: {topics}

Entities to research: {entities}
Research reason: {research_reason}

Return a JSON object where keys are entity names:
{{
  "EntityName": {{
    "description": "...",
    "category": "protocol|token|person|company|dao|chain|tool|other",
    "relevance": "...",
    "key_facts": ["fact1", "fact2"]
  }}
}}
"""


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
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY no definida")

    entities = item.get("entities") or []
    if not entities:
        logger.info("No hay entidades para investigar")
        return {}

    prompt = RESEARCH_PROMPT.format(
        title=item.get("title", ""),
        excerpt=item.get("excerpt", ""),
        source=item.get("source", ""),
        topics=", ".join(item.get("topics", [])),
        entities=", ".join(entities),
        research_reason=item.get("needs_research_reason", ""),
    )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    logger.info(f"Researching {len(entities)} entities with {RESEARCH_MODEL}...")

    response = client.messages.create(
        model=RESEARCH_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text
    research = _extract_json(raw_text)

    logger.info(f"Research complete: {list(research.keys())}")
    return research
