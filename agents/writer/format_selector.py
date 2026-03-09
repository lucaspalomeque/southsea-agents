"""Selecciona el formato editorial más adecuado según el contenido del brief.

Función pura con heurísticas simples. No usa LLM.
"""

import logging

logger = logging.getLogger(__name__)

BREAKING_KEYWORDS = [
    "urgente", "breaking", "just announced", "acaba de",
    "última hora", "de último momento", "just launched",
    "hack", "exploit", "crash", "colapso",
]

OPINION_KEYWORDS = [
    "regulación", "regulation", "geopolítica", "geopolitics",
    "prohibición", "ban", "censura", "censorship",
    "debate", "controversia", "controversial", "polémico",
    "debería", "should", "must", "necesita regularse",
]

EXPLAINER_KEYWORDS = [
    "nuevo protocolo", "new protocol", "qué es", "what is",
    "cómo funciona", "how it works", "entidad desconocida",
    "needs_research", "primera vez", "first time",
]


def _has_keywords(text: str, keywords: list[str]) -> bool:
    """Verifica si el texto contiene alguna de las keywords (case-insensitive)."""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def select_format(brief: dict, available_formats: list[str]) -> str:
    """Selecciona el formato editorial según señales del brief.

    Lógica de selección (en orden de prioridad):
    1. breaking: pocos verified_facts + señales de urgencia
    2. explainer: entidades investigadas + señales de explicación
    3. opinion: ángulo polémico sobre regulación/geopolítica
    4. analysis: default

    Solo retorna formatos que existen en available_formats.
    """
    editorial_angle = brief.get("editorial_angle", "")
    verified_facts = brief.get("verified_facts", [])
    research_notes = brief.get("research_notes", "")
    key_entities = brief.get("key_entities", [])
    context = brief.get("context", "")

    combined_text = f"{editorial_angle} {context}"

    # 1. Breaking: pocos datos verificados + urgencia
    if (
        "breaking" in available_formats
        and len(verified_facts) <= 2
        and _has_keywords(combined_text, BREAKING_KEYWORDS)
    ):
        logger.info(f"Formato seleccionado: breaking (pocos facts + urgencia)")
        return "breaking"

    # 2. Explainer: entidades investigadas
    if (
        "explainer" in available_formats
        and key_entities
        and (
            len(research_notes) > 100
            or _has_keywords(combined_text, EXPLAINER_KEYWORDS)
        )
    ):
        logger.info(f"Formato seleccionado: explainer (entidades investigadas)")
        return "explainer"

    # 3. Opinion: ángulo polémico
    if (
        "opinion" in available_formats
        and _has_keywords(editorial_angle, OPINION_KEYWORDS)
    ):
        logger.info(f"Formato seleccionado: opinion (ángulo polémico)")
        return "opinion"

    # 4. Default: analysis
    if "analysis" in available_formats:
        logger.info(f"Formato seleccionado: analysis (default)")
        return "analysis"

    # Fallback: primer formato disponible
    fallback = available_formats[0]
    logger.warning(f"Formato fallback: {fallback} (analysis no disponible)")
    return fallback
