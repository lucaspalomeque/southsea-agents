# CLAUDE.md — southsea-agents

> Este archivo es leído por Claude Code antes de trabajar en este repo.
> Contiene el contexto, las reglas y los patrones de trabajo para este proyecto.

---

## Qué es este proyecto

`southsea-agents` es el sistema de agentes autónomos de *The Southmetaverse Sea* — una editorial personal de IA que cubre Crypto/Web3/DeFi, Tecnología/IA y GenAI Art.

Este repo contiene los agentes que generan contenido 24/7. El contenido generado va a Supabase como `pending_review` y espera aprobación humana antes de publicarse.

**El repo relacionado** es `southmetaverse-sea` — el CMS y frontend donde se aprueba y visualiza el contenido. No modificar ese repo desde acá.

---

## Stack

- **Lenguaje:** Python 3.11+
- **Base de datos:** Supabase (PostgreSQL) via `supabase-py`
- **IA:** Anthropic Claude API (claude-sonnet como modelo principal)
- **Variables de entorno:** Siempre en `.env`, nunca hardcodeadas

---

## Estructura del proyecto

```
southsea-agents/
├── ARCHITECTURE.md         # Documento de arquitectura (leer antes de trabajar)
├── CLAUDE.md               # Este archivo
├── README.md               # Descripción pública del repo
├── .env                    # Variables de entorno (NO commitear)
├── .gitignore              # Incluye .env
│
├── agents/
│   ├── scout/              # Scout Agent: monitoreo de fuentes
│   ├── analyst/            # Analyst Agent: verificación y brief
│   ├── writer/             # Writer Agent: generación de borradores
│   ├── editor/             # Editor Agent: control de calidad
│   └── publisher/          # Publisher Agent: distribución a canales
│
├── core/
│   ├── supabase_client.py  # Cliente Supabase compartido
│   ├── models.py           # Modelos de datos (Post, Brief, etc.)
│   └── config.py           # Configuración global desde .env
│
├── specs/                  # Specs de cada agente (leer antes de implementar)
│   ├── scout.md
│   ├── analyst.md
│   ├── writer.md
│   ├── editor.md
│   └── publisher.md
│
└── docs/                   # Documentación adicional
```

---

## Reglas de trabajo

### Lo que siempre debés hacer
- Leer la spec del agente en `specs/` antes de implementar cualquier cosa
- Usar variables de entorno para todas las credenciales
- Manejar errores explícitamente — ningún agente puede crashear silenciosamente
- Escribir logs claros — cada acción del agente debe ser trazable
- Crear tests para cada función pública

### Lo que nunca debés hacer
- Hardcodear API keys, URLs o credenciales en el código
- Publicar contenido directamente — solo crear posts con `status: pending_review`
- Modificar posts con `status: published`
- Commitear el archivo `.env`
- Implementar features que no están en la spec sin consultar primero

---

## Variables de entorno requeridas

```bash
# .env — nunca commitear este archivo

SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...   # service key, no anon key

ANTHROPIC_API_KEY=sk-ant-...

# Canales de distribución (se agregan en fases posteriores)
# TWITTER_API_KEY=...
# SUBSTACK_API_KEY=...
```

---

## Cómo interactúan los agentes con Supabase

### Crear un borrador (acción principal de Writer Agent)

```python
from core.supabase_client import get_client

client = get_client()

post = {
    "title": "Título del artículo",
    "content": "Contenido en markdown...",
    "excerpt": "Resumen corto para redes",
    "tags": ["crypto", "defi"],
    "status": "pending_review",      # siempre pending_review, nunca published
    "created_by": "writer-agent",    # identificar el origen
    "original_language": "es",
}

result = client.table("posts").insert(post).execute()
```

### Invocar Edge Functions (opcional, para enriquecer contenido)

```python
import httpx

# Traducir el post automáticamente
response = httpx.post(
    f"{SUPABASE_URL}/functions/v1/translate-post",
    headers={"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"},
    json={"post_id": post_id}
)
```

### Edge Functions disponibles
- `format-content` — mejora estructura markdown
- `translate-post` — traduce ES↔EN automáticamente
- `analyze-post` — calcula reading time, sugiere splits
- `sync-knowledge` — actualiza embeddings RAG

---

## Estados del campo `status`

```
pending_review  → creado por agente, esperando aprobación humana  ← agentes solo escriben esto
published       → aprobado por humano y publicado                 ← agentes nunca escriben esto
draft           → borrador creado manualmente por humano          ← agentes no tocan esto
```

---

## Flujo de desarrollo

Antes de implementar cualquier agente:

```
1. Leer ARCHITECTURE.md          # entender el sistema completo
2. Leer specs/<agente>.md        # entender qué hace este agente específico
3. Implementar en agents/<agente>/
4. Testear con datos sintéticos antes de conectar a Supabase real
5. Logear cada acción con timestamp
```

---

## Patrones de código

### Estructura de un agente

```python
# agents/scout/scout_agent.py

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ScoutAgent:
    """
    Monitorea fuentes externas y recolecta información relevante.
    Ver specs/scout.md para el detalle completo.
    """

    def __init__(self, sources: list[str]):
        self.sources = sources
        logger.info(f"ScoutAgent inicializado con {len(sources)} fuentes")

    def run(self) -> list[dict]:
        """Ejecuta un ciclo de recolección."""
        logger.info(f"[{datetime.now()}] Scout iniciando ciclo")
        items = []
        for source in self.sources:
            try:
                new_items = self._fetch_source(source)
                items.extend(new_items)
                logger.info(f"  {source}: {len(new_items)} items nuevos")
            except Exception as e:
                logger.error(f"  {source}: error — {e}")
                continue  # un error en una fuente no detiene el resto
        return items

    def _fetch_source(self, source: str) -> list[dict]:
        raise NotImplementedError
```

### Manejo de errores

```python
# Siempre explícito, nunca silencioso
try:
    result = client.table("posts").insert(post).execute()
    logger.info(f"Post creado: {result.data[0]['id']}")
except Exception as e:
    logger.error(f"Error creando post: {e}")
    raise  # re-raise para que el orquestador lo maneje
```

---

## Temáticas cubiertas

Los agentes filtran y generan contenido sobre:
- **Crypto / Web3 / DeFi** — protocolos, mercados, on-chain data
- **Tecnología / IA** — modelos, herramientas, tendencias
- **GenAI Art** — arte generativo, modelos de imagen, cultura
- **Geopolítica** — con foco en impacto sobre crypto, IA y regulación tech
- **Startups** — ecosistema de IA y crypto, fundraising, nuevos builders

El filtro común: todo el contenido debe tener conexión directa con el universo crypto/IA. La geopolítica que importa es la que mueve mercados o regula tecnología. Las startups que importan son las que construyen en estos espacios.

Contenido fuera de estos temas debe descartarse en el Scout Agent.

---

## Voz editorial de la marca

*Detalle completo en `specs/writer.md`.*

La voz de The Southmetaverse Sea es una mezcla específica de cinco influencias:

- **Techno-optimista** — el futuro que construyen crypto e IA es mejor que el presente. Hay una postura, no neutralidad vacía.
- **Estilo Harari** — narrativas grandes que conectan lo micro con lo macro. Un protocolo DeFi no es solo código — es un capítulo de cómo los humanos coordinan valor. Claridad sin sacrificar profundidad.
- **Metáforas Borges** — lo técnico explicado con imágenes inesperadas. Lo fantástico como puerta de entrada a lo complejo. Un smart contract como un laberinto que se ejecuta solo.
- **d/acc (Defensive Acceleration)** — tecnología que empodera individuos y comunidades, no que concentra poder. Escepticismo hacia el control centralizado, optimismo hacia los sistemas abiertos.
- **The Network State** — las redes reemplazan a los estados. Las comunidades online se vuelven reales. La soberanía se construye con código y consenso, no con territorio.

Principios operacionales:
- Perspectiva propia, no reposteo neutro
- Tono analítico pero accesible
- Bilingüe (español e inglés)
- Rigor factual — si no se puede verificar, no se afirma

---

*southsea-agents · The Southmetaverse Sea · Marzo 2026*
