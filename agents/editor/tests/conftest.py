"""Fixtures y datos sintéticos para tests del Editor Agent."""

import os

# Setear env vars ANTES de que cualquier modulo las lea
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("AGENTS_API_KEY", "sk-test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key")


SYNTHETIC_POST = {
    "id": "post-001",
    "title": "Las Layer 2 de Ethereum superan los $20B: la escalabilidad se resuelve por capas",
    "content": (
        "## El récord silencioso\n\n"
        "Mientras el mercado crypto debate narrativas, las Layer 2 de Ethereum "
        "acaban de cruzar un umbral significativo: $20 mil millones en valor total bloqueado.\n\n"
        "## El mecanismo detrás del crecimiento\n\n"
        "Arbitrum lidera con $12.5B en TVL, seguido por Optimism con $7.8B. "
        "Ambos usan optimistic rollups, pero difieren en su enfoque de seguridad.\n\n"
        "El gas promedio en L2 es de $0.02 — comparado con $5.50 en mainnet. "
        "La migración no es ideológica, es económica.\n\n"
        "## Por qué importa\n\n"
        "Las transacciones mensuales en L2s crecieron 40% respecto al mes anterior. "
        "Esto no es especulación — es adopción real de infraestructura.\n\n"
        "## Implicaciones\n\n"
        "La escalabilidad de Ethereum no vendrá de un upgrade monolítico. "
        "Se está construyendo por capas, cada una optimizada para su caso de uso."
    ),
    "excerpt": "Las L2 de Ethereum superan $20B en TVL. La escalabilidad se resuelve por capas.",
    "tags": ["crypto_defi", "ethereum", "layer2"],
    "content_format": "analysis",
    "status": "pending_review",
    "created_by": "writer-agent",
    "analyst_brief_id": "brief-001",
    "revision_count": 0,
}

SYNTHETIC_POST_REVISION_2 = {
    **SYNTHETIC_POST,
    "id": "post-002",
    "revision_count": 2,
}

SYNTHETIC_POST_REVISION_3 = {
    **SYNTHETIC_POST,
    "id": "post-003",
    "revision_count": 3,
}

SYNTHETIC_BRIEF = {
    "id": "brief-001",
    "title": "Ethereum Layer 2 alcanza nuevo récord de TVL",
    "context": (
        "Arbitrum y Optimism superaron los $20B combinados en TVL. "
        "El crecimiento fue impulsado por migración de protocolos DeFi."
    ),
    "key_entities": ["Arbitrum", "Optimism", "Ethereum"],
    "editorial_angle": "El crecimiento de L2s indica escalabilidad por capas.",
    "verified_facts": [
        "Arbitrum TVL: $12.5B (fuente: DefiLlama)",
        "Optimism TVL: $7.8B (fuente: DefiLlama)",
        "Transacciones mensuales en L2s: +40% vs mes anterior",
        "Gas promedio en L2: $0.02 vs $5.50 en mainnet",
    ],
    "research_notes": "Ambos L2s usan optimistic rollups.",
}

SYNTHETIC_VOICE = """# Voice Guide
Tono analítico, perspectiva propia, sin relleno.
Influencias: Dalio (mecanismo), Harari (narrativa macro), Balaji (tesis con datos).
"""

SYNTHETIC_FORMAT_ANALYSIS = """# Formato: Analysis
600-1200 palabras. Estructura: gancho, mecanismo, por qué importa, implicaciones.
"""

SYNTHETIC_FORMATS = {
    "analysis": SYNTHETIC_FORMAT_ANALYSIS,
    "breaking": "# Formato: Breaking\n200-400 palabras.",
    "explainer": "# Formato: Explainer\n300-600 palabras.",
    "opinion": "# Formato: Opinion\n400-800 palabras.",
}

SYNTHETIC_LLM_EVALUATION_APPROVED = """{
    "voice_alignment": 8.0,
    "factual_rigor": 7.5,
    "format_compliance": 9.0,
    "thematic_alignment": 8.5,
    "feedback": "Buen artículo. El tono es analítico y la estructura respeta el formato analysis. Los datos coinciden con el brief."
}"""

SYNTHETIC_LLM_EVALUATION_VETO = """{
    "voice_alignment": 8.0,
    "factual_rigor": 3.0,
    "format_compliance": 9.0,
    "thematic_alignment": 8.5,
    "feedback": "El artículo inventa datos que no están en el brief. Rigor factual insuficiente."
}"""

SYNTHETIC_LLM_EVALUATION_WRAPPED = """```json
{
    "voice_alignment": 7.0,
    "factual_rigor": 6.5,
    "format_compliance": 8.0,
    "thematic_alignment": 7.5,
    "feedback": "Artículo correcto, puede mejorar la conexión con tesis Balaji."
}
```"""

SYNTHETIC_SAVED_REVIEW = {
    "id": "review-001",
    "post_id": "post-001",
    "decision": "approved",
}
