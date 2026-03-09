"""Fixtures y datos sintéticos para tests del Writer Agent."""

import os

# Setear env vars ANTES de que cualquier modulo las lea
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co/functions/v1/agent-ingest")
os.environ.setdefault("AGENTS_API_KEY", "sk-test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key")


SYNTHETIC_BRIEF = {
    "id": "brief-001",
    "title": "Ethereum Layer 2 alcanza nuevo récord de TVL",
    "context": (
        "Arbitrum y Optimism superaron los $20B combinados en TVL. "
        "El crecimiento fue impulsado por migración de protocolos DeFi "
        "que buscan costos de transacción más bajos. Los datos on-chain "
        "muestran un incremento del 40% en transacciones mensuales."
    ),
    "key_entities": ["Arbitrum", "Optimism", "Ethereum"],
    "editorial_angle": (
        "El crecimiento de L2s indica que la escalabilidad de Ethereum "
        "se está resolviendo por capas, no por reemplazo. Análisis del "
        "impacto en el ecosistema DeFi."
    ),
    "verified_facts": [
        "Arbitrum TVL: $12.5B (fuente: DefiLlama)",
        "Optimism TVL: $7.8B (fuente: DefiLlama)",
        "Transacciones mensuales en L2s: +40% vs mes anterior",
        "Gas promedio en L2: $0.02 vs $5.50 en mainnet",
    ],
    "research_notes": "Ambos L2s usan optimistic rollups. Arbitrum usa fraud proofs, Optimism migra a fault proofs.",
    "topics": ["crypto_defi", "ethereum", "layer2"],
    "status": "pending_writing",
}

SYNTHETIC_BRIEF_BREAKING = {
    "id": "brief-002",
    "title": "Hack masivo en protocolo DeFi",
    "context": "Un exploit acaba de drenar fondos de un protocolo DeFi importante.",
    "key_entities": ["ProtocoloX"],
    "editorial_angle": "Urgente: exploit confirmado, pérdidas en curso",
    "verified_facts": ["$50M drenados según datos on-chain"],
    "research_notes": "",
    "topics": ["crypto_defi", "security"],
    "status": "pending_writing",
}

SYNTHETIC_BRIEF_EXPLAINER = {
    "id": "brief-003",
    "title": "Qué es EigenLayer y cómo funciona el restaking",
    "context": "EigenLayer introduce un nuevo paradigma en seguridad compartida para Ethereum.",
    "key_entities": ["EigenLayer", "Restaking"],
    "editorial_angle": "Nuevo protocolo que necesita explicación para entender su impacto",
    "verified_facts": [
        "EigenLayer permite reutilizar ETH stakeado",
        "$10B en TVL en 3 meses",
    ],
    "research_notes": (
        "EigenLayer es un protocolo de restaking en Ethereum que permite a los stakers "
        "de ETH reutilizar su stake para asegurar otros servicios (AVS - Actively Validated Services). "
        "Esto crea un marketplace de seguridad compartida. El riesgo es el slashing acumulado."
    ),
    "topics": ["crypto_defi", "ethereum"],
    "status": "pending_writing",
}

SYNTHETIC_BRIEF_OPINION = {
    "id": "brief-004",
    "title": "La SEC vs DeFi: regulación que mata la innovación",
    "context": "La SEC intensifica acciones contra protocolos DeFi.",
    "key_entities": ["SEC", "Uniswap"],
    "editorial_angle": "Regulación excesiva que amenaza la innovación en DeFi — debate polémico",
    "verified_facts": [
        "SEC envió Wells Notice a Uniswap Labs",
        "3 protocolos DeFi multados en Q1 2026",
    ],
    "research_notes": "Uniswap argumenta que el protocolo es descentralizado y no es un exchange.",
    "topics": ["crypto_defi", "regulation"],
    "status": "pending_writing",
}

SYNTHETIC_VOICE = """# Voice Guide
Tono analítico, perspectiva propia, sin relleno.
Influencias: Dalio (mecanismo), Harari (narrativa macro), Balaji (tesis con datos).
"""

SYNTHETIC_FORMAT_ANALYSIS = """# Formato: Analysis
600-1200 palabras. Estructura: gancho, mecanismo, por qué importa, implicaciones.
"""

SYNTHETIC_FORMAT_BREAKING = """# Formato: Breaking
200-400 palabras. Estructura: el hecho, contexto rápido, qué mirar.
"""

SYNTHETIC_FORMATS = {
    "analysis": SYNTHETIC_FORMAT_ANALYSIS,
    "breaking": SYNTHETIC_FORMAT_BREAKING,
    "explainer": "# Formato: Explainer\n300-600 palabras.",
    "opinion": "# Formato: Opinion\n400-800 palabras.",
}

SYNTHETIC_LLM_RESPONSE = """===TITLE===
Las Layer 2 de Ethereum superan los $20B: la escalabilidad se resuelve por capas
===CONTENT===
## El récord silencioso

Mientras el mercado crypto debate narrativas, las Layer 2 de Ethereum acaban de cruzar un umbral significativo: $20 mil millones en valor total bloqueado.

## El mecanismo detrás del crecimiento

Arbitrum lidera con $12.5B en TVL, seguido por Optimism con $7.8B. Ambos usan optimistic rollups, pero difieren en su enfoque de seguridad.

El gas promedio en L2 es de $0.02 — comparado con $5.50 en mainnet. La migración no es ideológica, es económica.

## Por qué importa

Las transacciones mensuales en L2s crecieron 40% respecto al mes anterior. Esto no es especulación — es adopción real de infraestructura.

## Implicaciones

La escalabilidad de Ethereum no vendrá de un upgrade monolítico. Se está construyendo por capas, cada una optimizada para su caso de uso.
===EXCERPT===
Las L2 de Ethereum superan $20B en TVL. Arbitrum y Optimism lideran una migración que no es ideológica — es económica. La escalabilidad se resuelve por capas."""
