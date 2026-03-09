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
- **Base de datos:** Supabase (PostgreSQL) via Edge Functions + httpx
- **IA:** Anthropic Claude API via `core/llm_client.py` (Haiku para clasificación, Sonnet para research/escritura). Soporta Anthropic y OpenRouter como providers
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
│   ├── supabase_client.py  # Cliente Supabase compartido (ingest via Edge Functions)
│   ├── llm_client.py       # Abstracción LLM: completion() con soporte Anthropic + OpenRouter
│   ├── model_config.py     # Modelos por tarea (scout.classifier, writer.content_generator, etc.)
│   ├── models.py           # Modelos de datos (Post, Brief, etc.)
│   └── config.py           # Configuración global desde .env
│
├── editorial/
│   ├── voice.md            # Guía de voz editorial (system prompt del Writer)
│   └── formats/            # Templates de formato (analysis, breaking, explainer, opinion)
│
├── scripts/                # Runners para ejecutar agentes manualmente
│
├── specs/                  # Specs de cada agente (leer antes de implementar)
│   ├── scout.md
│   ├── analyst.md
│   ├── writer.md
│   ├── editor.md           # pendiente
│   └── publisher.md        # pendiente
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
AGENTS_API_KEY=...             # clave compartida para autenticar agentes con Edge Functions

ANTHROPIC_API_KEY=sk-ant-...   # requerida por agentes que usan Claude directo
OPENROUTER_API_KEY=...         # provider alternativo (opcional)

# Canales de distribución (se agregan en fases posteriores)
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHANNEL_NAMES=...
```

---

## Edge Functions de agentes

Los agentes no usan `supabase-py` directamente. Toda la comunicación con Supabase pasa por tres Edge Functions autenticadas con `x-agent-key`:

| Edge Function    | Método | Acción  | Payload                              |
|------------------|--------|---------|--------------------------------------|
| `agent-ingest`   | POST   | INSERT  | `{table, ...campos}`                |
| `agent-read`     | POST   | SELECT  | `{table, filters, limit}`           |
| `agent-update`   | POST   | UPDATE  | `{table, id, updates}`              |

Header de autenticación:
```
x-agent-key: <AGENTS_API_KEY>
Content-Type: application/json
```

---

## Cómo interactúan los agentes con Supabase

### Insertar un registro (via agent-ingest)

```python
import httpx
from core.config import SUPABASE_URL, AGENTS_API_KEY

HEADERS = {
    "x-agent-key": AGENTS_API_KEY,
    "Content-Type": "application/json",
}

response = httpx.post(
    f"{SUPABASE_URL}/functions/v1/agent-ingest",
    headers=HEADERS,
    json={
        "table": "scout_items",
        "title": "Título del item",
        "source": "coindesk",
        "status": "pending_analysis",
    },
    timeout=30,
)
response.raise_for_status()
```

### Leer registros (via agent-read)

```python
response = httpx.post(
    f"{SUPABASE_URL}/functions/v1/agent-read",
    headers=HEADERS,
    json={
        "table": "scout_items",
        "filters": {"status": "pending_analysis"},
        "limit": 10,
    },
    timeout=30,
)
items = response.json()["data"]
```

### Actualizar un registro (via agent-update)

```python
response = httpx.post(
    f"{SUPABASE_URL}/functions/v1/agent-update",
    headers=HEADERS,
    json={
        "table": "scout_items",
        "id": item_id,
        "updates": {"status": "analyzed"},
    },
    timeout=30,
)
```

### Edge Functions de contenido (opcionales)
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

Definida en `editorial/voice.md` (se inyecta como system prompt del Writer Agent). Tres influencias principales: **Ray Dalio** (mecanismos), **Yuval Harari** (narrativa macro), **Balaji Srinivasan** (tesis con datos).

Los formatos editoriales viven en `editorial/formats/`: analysis, breaking, explainer, opinion. El Writer selecciona el formato automáticamente según el contenido del brief.

No modificar estos archivos sin revisar el output del pipeline — son documentos vivos que se iteran viendo resultados.

---

## Estado actual de los agentes

| Agente | Estado | Notas |
|--------|--------|-------|
| **Scout** | ✅ Funcional | RSS (CoinDesk, a16z YT, YC YT). 3 feeds rotos (bankless, coin_bureau, yt_network_state). Clasifica con Haiku. |
| **Analyst** | ✅ Funcional | Genera briefs editoriales con Sonnet. Research condicional por entidad. |
| **Writer** | ✅ Funcional | Artículos con formato automático (analysis/breaking/explainer/opinion). Genera slug, guarda como `pending_review`. Traducción via translate-post (pendiente fix auth). |
| **Editor** | ⏳ Pendiente | Spec por escribir. |
| **Publisher** | ⏳ Pendiente | Spec por escribir. |

Pipeline end-to-end probado: Scout → Analyst → Writer con datos reales de RSS.

---

*southsea-agents · The Southmetaverse Sea · Marzo 2026*
