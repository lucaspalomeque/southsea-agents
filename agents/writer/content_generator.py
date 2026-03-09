"""Genera artículos editoriales usando Claude Sonnet.

Combina voice guide + formato seleccionado + brief para producir
un artículo en español con título, contenido markdown y excerpt.
"""

import json
import logging

from core.llm_client import completion
from core.model_config import MODELS

logger = logging.getLogger(__name__)

MODEL = MODELS["writer.content_generator"]

DELIMITER_TITLE = "===TITLE==="
DELIMITER_CONTENT = "===CONTENT==="
DELIMITER_EXCERPT = "===EXCERPT==="


def _build_user_prompt(brief: dict, format_template: str, format_name: str) -> str:
    """Construye el prompt de usuario con el brief y el formato."""
    entities_str = json.dumps(brief.get("key_entities", []), ensure_ascii=False)
    facts_str = "\n".join(f"- {f}" for f in brief.get("verified_facts", []))

    return f"""## Formato editorial a usar: {format_name}

{format_template}

---

## Brief del Analyst

**Título de trabajo:** {brief.get("title", "Sin título")}

**Ángulo editorial:** {brief.get("editorial_angle", "No especificado")}

**Contexto:**
{brief.get("context", "Sin contexto")}

**Entidades clave:** {entities_str}

**Datos verificados:**
{facts_str or "No hay datos verificados"}

**Notas de investigación:**
{brief.get("research_notes", "Sin notas adicionales")}

---

## Instrucciones de output

Generá el artículo en español siguiendo el formato editorial indicado arriba.
Usá la voz editorial del system prompt.

Respondé EXACTAMENTE con este formato (respetá los delimitadores):

{DELIMITER_TITLE}
[Título del artículo — tesis, no descripción del evento]
{DELIMITER_CONTENT}
[Contenido completo en markdown. Usá ## para secciones. Respetá el rango de palabras del formato.]
{DELIMITER_EXCERPT}
[Resumen para redes sociales. Máximo 280 caracteres. Debe funcionar como tweet independiente.]"""


def _parse_response(response: str) -> dict:
    """Parsea la respuesta del LLM extrayendo título, contenido y excerpt.

    Raises:
        ValueError: Si la respuesta no tiene los delimitadores esperados.
    """
    if DELIMITER_TITLE not in response:
        raise ValueError(f"Respuesta del LLM no contiene {DELIMITER_TITLE}")
    if DELIMITER_CONTENT not in response:
        raise ValueError(f"Respuesta del LLM no contiene {DELIMITER_CONTENT}")
    if DELIMITER_EXCERPT not in response:
        raise ValueError(f"Respuesta del LLM no contiene {DELIMITER_EXCERPT}")

    # Split by delimiters
    after_title = response.split(DELIMITER_TITLE, 1)[1]
    title_raw, rest = after_title.split(DELIMITER_CONTENT, 1)
    content_raw, excerpt_raw = rest.split(DELIMITER_EXCERPT, 1)

    title = title_raw.strip()
    content = content_raw.strip()
    excerpt = excerpt_raw.strip()

    # Truncar excerpt a 280 chars si el LLM se excedió
    if len(excerpt) > 280:
        logger.warning(f"Excerpt excede 280 chars ({len(excerpt)}), truncando")
        excerpt = excerpt[:277] + "..."

    if not title:
        raise ValueError("El LLM retornó un título vacío")
    if not content:
        raise ValueError("El LLM retornó contenido vacío")

    return {
        "title": title,
        "content": content,
        "excerpt": excerpt,
    }


def generate_article(brief: dict, voice: str, format_template: str, format_name: str) -> dict:
    """Genera un artículo editorial a partir de un brief.

    Args:
        brief: Brief del Analyst con contexto, ángulo, datos.
        voice: Contenido de voice.md (se usa como system prompt).
        format_template: Contenido del formato .md seleccionado.
        format_name: Nombre del formato (analysis, breaking, etc.).

    Returns:
        Dict con keys: title, content, excerpt.

    Raises:
        ValueError: Si la respuesta del LLM no se puede parsear.
    """
    user_prompt = _build_user_prompt(brief, format_template, format_name)

    logger.info(f"Generando artículo — formato: {format_name}, brief: {brief.get('title', '?')}")

    response = completion(
        model=MODEL,
        messages=[{"role": "user", "content": user_prompt}],
        max_tokens=4096,
        system=voice,
    )

    article = _parse_response(response)
    logger.info(
        f"Artículo generado — título: {article['title'][:50]}... "
        f"contenido: {len(article['content'])} chars, "
        f"excerpt: {len(article['excerpt'])} chars"
    )
    return article
