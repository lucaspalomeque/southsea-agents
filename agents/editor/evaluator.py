"""Evalúa posts editoriales usando Claude Haiku.

4 dimensiones de evaluación:
- voice_alignment: alineación con la voz editorial de la marca
- factual_rigor: rigor factual respecto al brief del analyst
- format_compliance: cumplimiento del formato asignado
- thematic_alignment: relevancia temática (crypto/DeFi, tech/IA, GenAI art)

Regla de veto: si cualquier dimensión < 4.0, el post se devuelve.
"""

import json
import logging

from core.llm_client import completion
from core.model_config import MODELS

logger = logging.getLogger(__name__)

MODEL = MODELS["editor.evaluator"]

DIMENSIONS = ["voice_alignment", "factual_rigor", "format_compliance", "thematic_alignment"]

VETO_THRESHOLD = 4.0

SYSTEM_PROMPT = """Sos el Editor Agent de The Southmetaverse Sea, una editorial de IA que cubre Crypto/Web3/DeFi, Tech/IA y GenAI Art.

Tu trabajo es evaluar borradores editoriales en 4 dimensiones, con un score de 1.0 a 10.0 cada una.

## Guía de voz editorial

{voice}

## Dimensiones de evaluación

1. **voice_alignment** (1-10): ¿El artículo respeta la voz editorial? Tono analítico, perspectiva propia, influencias Dalio (mecanismo), Harari (narrativa macro), Balaji (tesis con datos). Sin relleno, sin neutralidad vacía.

2. **factual_rigor** (1-10): ¿Los datos del artículo coinciden con los del brief? ¿Hay afirmaciones sin respaldo? ¿Se inventaron datos o fuentes?

3. **format_compliance** (1-10): ¿El artículo cumple con la estructura del formato asignado? ¿El largo es correcto? ¿El markdown está bien formateado? ¿Tiene las secciones esperadas?

4. **thematic_alignment** (1-10): ¿El contenido es relevante para las temáticas de la marca (Crypto/DeFi, Tech/IA, GenAI Art, geopolítica tech, startups crypto/IA)?

Respondé SIEMPRE en JSON válido con este formato exacto:

```json
{{
    "voice_alignment": 8.0,
    "factual_rigor": 7.5,
    "format_compliance": 9.0,
    "thematic_alignment": 8.5,
    "feedback": "Feedback específico sobre qué mejorar. Si todo está bien, decí qué está bien."
}}
```

Sé específico en el feedback. Si algo falla, explicá exactamente qué y cómo mejorarlo."""


def _build_user_prompt(post: dict, brief: dict | None, format_template: str) -> str:
    """Construye el prompt de usuario con el post, brief y formato."""
    brief_section = ""
    if brief:
        facts_str = "\n".join(f"- {f}" for f in brief.get("verified_facts", []))
        brief_section = f"""## Brief del Analyst (referencia factual)

**Título:** {brief.get("title", "N/A")}
**Ángulo editorial:** {brief.get("editorial_angle", "N/A")}
**Datos verificados:**
{facts_str or "No hay datos verificados"}
**Contexto:** {brief.get("context", "N/A")}"""
    else:
        brief_section = "## Brief del Analyst\nNo disponible — evaluar rigor factual con lo que hay en el artículo."

    return f"""## Post a evaluar

**Título:** {post.get("title", "Sin título")}
**Formato asignado:** {post.get("content_format", "desconocido")}
**Excerpt:** {post.get("excerpt", "Sin excerpt")}
**Tags:** {json.dumps(post.get("tags", []), ensure_ascii=False)}

### Contenido del artículo

{post.get("content", "Sin contenido")}

---

{brief_section}

---

## Formato editorial esperado

{format_template}

---

Evaluá este artículo en las 4 dimensiones. Respondé SOLO con JSON válido."""


def _parse_evaluation(response: str) -> dict:
    """Parsea la respuesta JSON del LLM.

    Raises:
        ValueError: Si la respuesta no es JSON válido o faltan campos.
    """
    # Extraer JSON si viene envuelto en markdown code block
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json) and last line (```)
        json_lines = []
        inside = False
        for line in lines:
            if line.strip().startswith("```") and not inside:
                inside = True
                continue
            if line.strip() == "```" and inside:
                break
            if inside:
                json_lines.append(line)
        text = "\n".join(json_lines)

    data = json.loads(text)

    for dim in DIMENSIONS:
        if dim not in data:
            raise ValueError(f"Falta dimensión '{dim}' en la respuesta del LLM")
        score = float(data[dim])
        if not (1.0 <= score <= 10.0):
            raise ValueError(f"Score de '{dim}' fuera de rango: {score}")
        data[dim] = score

    if "feedback" not in data:
        raise ValueError("Falta 'feedback' en la respuesta del LLM")

    return data


def evaluate(post: dict, brief: dict | None, voice: str, format_template: str) -> dict:
    """Evalúa un post editorial en 4 dimensiones.

    Args:
        post: Post a evaluar (title, content, excerpt, tags, content_format).
        brief: Brief del Analyst asociado (puede ser None si no se encontró).
        voice: Contenido de voice.md.
        format_template: Contenido del formato .md asignado.

    Returns:
        Dict con keys: scores (dict), average_score (float),
        decision (str), feedback (str).

    Raises:
        ValueError: Si la respuesta del LLM no se puede parsear.
    """
    system = SYSTEM_PROMPT.format(voice=voice)
    user_prompt = _build_user_prompt(post, brief, format_template)

    logger.info(f"Evaluando post: {post.get('title', '?')[:50]}")

    response = completion(
        model=MODEL,
        messages=[{"role": "user", "content": user_prompt}],
        max_tokens=1024,
        system=system,
    )

    data = _parse_evaluation(response)

    scores = {dim: data[dim] for dim in DIMENSIONS}
    average_score = sum(scores.values()) / len(scores)

    # Regla de veto: cualquier dimensión < 4.0 → devolver
    veto = any(score < VETO_THRESHOLD for score in scores.values())
    decision = "needs_revision" if veto else "approved"

    result = {
        "scores": scores,
        "average_score": round(average_score, 2),
        "decision": decision,
        "feedback": data["feedback"],
    }

    logger.info(
        f"Evaluación completada — decision: {decision}, "
        f"average: {average_score:.2f}, "
        f"scores: {scores}"
    )
    return result
