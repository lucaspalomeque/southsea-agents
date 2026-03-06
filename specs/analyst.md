# Spec: Analyst Agent

## Rol
El Analyst es el segundo agente del pipeline editorial de The Southmetaverse Sea.
Su trabajo es tomar items crudos del Scout, investigar entidades desconocidas,
y producir briefs estructurados que el Writer usará para generar artículos.

El Analyst no escribe contenido editorial. Analiza, verifica y estructura.

---

## Frecuencia de ejecución
Cada 6 horas, después del Scout: 01:00 / 07:00 / 13:00 / 19:00 UTC
(1 hora después de cada ciclo del Scout para dar tiempo a que los items se acumulen)

---

## Pipeline por item

```
1. Leer scout_items con status=pending_analysis (via agent-read)
2. Para cada item:
   a. Marcar como in_analysis (via agent-update)
   b. Si needs_research=true → investigar entidades con Claude Sonnet
   c. Construir brief estructurado (Claude Sonnet)
   d. Guardar brief en analyst_briefs (via agent-ingest)
   e. Marcar scout_item como processed (via agent-update)
3. Si un item falla → restaurar status a pending_analysis (rollback)
```

---

## Modelo de IA

**Claude Sonnet** (`claude-sonnet-4-20250514`) para ambos pasos (research y brief).
El Analyst necesita razonamiento, no solo clasificación — por eso usa Sonnet en vez de Haiku.

---

## Endpoints de Supabase

Todos autenticados con header `x-agent-key`.

| Endpoint | Método | Body | Uso |
|----------|--------|------|-----|
| agent-read | POST | `{table, filters, limit}` | Leer scout_items pendientes |
| agent-ingest | POST | `{table, record}` | Guardar briefs |
| agent-update | POST | `{table, id, updates}` | Actualizar status de scout_items |

---

## Tabla: `analyst_briefs`

```sql
create table analyst_briefs (
  id uuid primary key default gen_random_uuid(),
  scout_item_id uuid references scout_items(id),
  title text not null,
  context text not null,
  key_entities jsonb not null,
  editorial_angle text not null,
  verified_facts text[] not null,
  research_notes text,
  created_at timestamptz default now(),
  status text default 'pending_writing'
  -- status values:
  -- pending_writing  → esperando al Writer
  -- in_writing       → Writer trabajando
  -- written          → Writer terminó
);
```

---

## Campos del brief

| Campo | Tipo | Descripción |
|-------|------|-------------|
| title | text | Título editorial (no copia del original) |
| context | text | 2-3 párrafos de contexto y background |
| key_entities | jsonb | Array de {name, description, role_in_story} |
| editorial_angle | text | Tesis y perspectiva para el Writer |
| verified_facts | text[] | Hechos verificados que se pueden afirmar |
| research_notes | text | Caveats, claims sin verificar, contexto extra |

---

## Investigación de entidades

Cuando un scout_item tiene `needs_research=true`, el Analyst investiga las entidades
listadas usando Claude Sonnet. Por cada entidad produce:

```json
{
  "description": "Qué es (1-2 oraciones)",
  "category": "protocol|token|person|company|dao|chain|tool|other",
  "relevance": "Por qué importa en crypto/AI",
  "key_facts": ["hecho verificado 1", "hecho verificado 2"]
}
```

Si `needs_research=false`, se salta este paso y va directo al brief.

---

## Manejo de errores

- Si un item falla en cualquier paso, su status vuelve a `pending_analysis`
- Un error en un item no detiene el procesamiento de los demás
- Todos los errores se loguean con item_id y detalle
- Si Claude retorna un brief incompleto (faltan campos), se lanza ValueError

---

## Lo que el Analyst NO hace

- No genera contenido editorial (eso es del Writer)
- No publica en ningún canal
- No modifica posts con status `published`
- No toma decisiones de publicación
- No escribe en la tabla `posts`

---

## Estructura de archivos

```
agents/analyst/
├── __init__.py
├── analyst_agent.py       # Orquestador del pipeline
├── researcher.py          # Investigación de entidades con Claude Sonnet
├── brief_builder.py       # Construcción del brief estructurado
├── supabase_io.py         # Comunicación con Supabase (read/ingest/update)
└── tests/
    ├── __init__.py
    ├── conftest.py            # Env vars dummy para tests
    ├── test_analyst_agent.py  # Tests del pipeline completo (mocks)
    ├── test_brief_builder.py  # Tests del brief builder (mock Claude)
    ├── test_researcher.py     # Tests del researcher (mock Claude)
    └── test_supabase_io.py    # Tests de IO (mock httpx)
```

---

## Variables de entorno requeridas

```bash
SUPABASE_URL=...          # Base URL de Supabase (ya configurada)
AGENTS_API_KEY=...        # API key para Edge Functions (ya configurada)
ANTHROPIC_API_KEY=...     # Para Claude Sonnet
```

---

## Output esperado por ciclo

Cada ejecución produce:
- N briefs guardados en `analyst_briefs` con `status: pending_writing`
- N scout_items actualizados a `status: processed`
- Log de ejecución con: items procesados, errores, tiempo total
- Sin errores silenciosos

---

*specs/analyst.md · southsea-agents · Marzo 2026*
