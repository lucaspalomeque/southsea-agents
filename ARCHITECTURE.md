# ARCHITECTURE.md — southsea-agents

> Documento interno. Explica qué es este sistema, cómo funciona, y por qué se tomaron las decisiones que se tomaron.
> Última actualización: Marzo 2026

---

## Qué es este sistema

**southsea-agents** es el motor autónomo de contenido de *The Southmetaverse Sea* — una editorial personal de IA que cubre Crypto/Web3/DeFi, Tecnología/IA y GenAI Art.

Este repo contiene los agentes de IA que trabajan 24/7 para:
1. Monitorear fuentes de información relevantes
2. Analizar y verificar contenido
3. Generar borradores editoriales
4. Esperar aprobación humana
5. Publicar en los canales correspondientes
6. Aprender del feedback para mejorar iteración a iteración

**Lo que este repo NO es:**
- No es el CMS ni el frontend (eso vive en el repo `southmetaverse-sea`)
- No es un bot de reposteo — genera contenido editorial con voz propia
- No publica nada sin aprobación humana

---

## Los dos repositorios

Este sistema tiene dos repos que comparten la misma base de datos:

```
southsea-agents  (este repo)     southmetaverse-sea (CMS)
Python · Agentes · 24/7          React · Frontend · Lovable

         │                                  │
         └──────────────┬───────────────────┘
                        ▼
                   Supabase
                  PostgreSQL
                        │
                        ▼
          X / Blog / Substack / Moltbook
```

**Regla de convivencia:** Los agentes escriben a Supabase. El CMS lee de Supabase. Nunca se tocan entre sí. El CMS no sabe que existen los agentes. Los agentes no saben que existe el CMS.

---

## Los dos loops del sistema

### Loop 1 — Producción (el ciclo de cada pieza de contenido)

```
Fuentes externas
      │
      ▼
Scout Agent         → recolecta y filtra información relevante
      │
      ▼
Analyst Agent       → verifica datos, agrega contexto, arma brief
      │
      ▼
Writer Agent        → genera el borrador con voz editorial de la marca
      │
      ▼
Editor Agent        → revisa calidad, coherencia y alineación con la marca
      │
      ▼
Supabase            → guarda como status: pending_review
      │
      ▼
[HUMANO APRUEBA]    → desde el dashboard del CMS
      │
      ▼
Publisher Agent     → formatea y distribuye a cada canal
      │
      ▼
X / Blog / Substack / Moltbook
```

### Loop 2 — Aprendizaje (cómo el sistema mejora con el tiempo)

```
Humano aprueba / rechaza / edita un borrador
      │
      ▼
El sistema registra la decisión con contexto
(por qué se aprobó, qué se editó, qué se rechazó)
      │
      ▼
Editor Agent actualiza sus criterios editoriales
      │
      ▼
El próximo borrador está más alineado con la voz de la marca
```

Con el tiempo, el Editor Agent necesita menos intervención humana porque aprendió los criterios del editor.

---

## Los agentes

### Scout Agent
**Rol:** Monitoreo y recolección de información 24/7
**Input:** Lista de fuentes configuradas (RSS, X/Twitter, newsletters, on-chain data)
**Output:** Items filtrados y clasificados guardados en la DB
**Criterio de filtrado:** Relevancia temática (Crypto/Web3/DeFi, Tech/AI, GenAI Art) + señal/ruido

### Analyst Agent
**Rol:** Verificación y enriquecimiento de información
**Input:** Items del Scout
**Output:** Brief estructurado con datos verificados, contexto y ángulo editorial sugerido
**Responsabilidad:** No inventa datos. Si no puede verificar algo, lo marca como no verificado.

### Writer Agent
**Rol:** Generación de borradores editoriales
**Input:** Brief del Analyst
**Output:** Borrador completo con título, contenido, excerpt y tags sugeridos
**Voz:** Editorial propia de The Southmetaverse Sea (a definir en detalle en la spec)
**Formatos:** Artículo largo (blog/Substack), hilo (X), post corto (Moltbook)

### Editor Agent
**Rol:** Control de calidad antes de la revisión humana
**Input:** Borrador del Writer
**Output:** Borrador aprobado para revisión humana, o borrador devuelto al Writer con comentarios
**Criterio:** Voz de la marca, rigor factual, formato correcto, alineación temática
**Aprendizaje:** Actualiza sus criterios basándose en las decisiones del editor humano

### Publisher Agent
**Rol:** Distribución a canales externos
**Input:** Post aprobado por el humano (status: published en Supabase)
**Output:** Contenido publicado en X, Blog, Substack y Moltbook
**Regla de oro:** Solo actúa sobre posts con status `published`. Nunca publica sin aprobación.

---

## Base de datos (Supabase)

### Tabla principal: `posts`

Los agentes trabajan principalmente con esta tabla. Los campos más relevantes:

| Campo | Uso por agentes |
|-------|----------------|
| `title` / `title_en` / `title_es` | El Writer genera el título en ambos idiomas |
| `content` / `content_en` / `content_es` | Contenido principal + traducciones |
| `excerpt` | Resumen para distribución en redes |
| `tags` | Clasificación temática |
| `status` | El campo de control del flujo editorial |
| `created_by` | Identifica qué agente o humano creó la nota |
| `cover_image` | URL de imagen de portada (opcional para agentes) |
| `slug` | Generado automáticamente desde el título |

### Estados del campo `status`

```
draft          → borrador creado por humano (flujo manual)
pending_review → borrador creado por agente, esperando aprobación humana
published      → aprobado y publicado
```

### Campo `created_by`

Identifica el origen de cada pieza de contenido:
- `human` → creado desde el CMS manualmente
- `scout-agent` → generado por el pipeline de agentes
- `writer-agent` → (si se necesita granularidad mayor)

### Edge Functions disponibles (ya existen en el CMS)

Los agentes pueden invocar estas funciones para enriquecer el contenido:

| Función | Qué hace |
|---------|---------|
| `format-content` | Mejora la estructura markdown con Gemini |
| `translate-post` | Traduce automáticamente ES↔EN |
| `analyze-post` | Calcula reading time, sugiere splits |
| `sync-knowledge` | Actualiza embeddings RAG |

---

## Cómo se autentica un agente con Supabase

Los agentes usan la **service key** de Supabase (acceso admin, bypasea RLS). Esta key vive en un archivo `.env` local y **nunca se commitea al repo**.

```python
from supabase import create_client

client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")  # nunca en el código, siempre en .env
)
```

---

## Canales de distribución

| Canal | Tipo de contenido | Formato |
|-------|------------------|---------|
| X / Twitter | Análisis corto, threads | Hilos de 3-8 tweets |
| Blog (southmetaversesea.com) | Artículos completos | Markdown largo |
| Substack | Newsletter / artículos | Formato Substack |
| Moltbook | Posts cortos | Formato nativo |

Cada canal tiene su formato. El Writer Agent genera el contenido base y el Publisher Agent lo adapta a cada canal.

---

## Decisiones técnicas y por qué

**¿Por qué Python y no TypeScript?**
El ecosistema de IA en Python es más maduro. Las librerías de orquestación de agentes (LangChain, CrewAI, o llamadas directas a la API de Anthropic) son más naturales en Python. El CMS en TypeScript no necesita saber que los agentes existen.

**¿Por qué repos separados y no monorepo?**
Los agentes y el CMS tienen ciclos de vida diferentes. El CMS se deploya en Lovable. Los agentes corren en local o en un servidor. Mezclarlos agrega complejidad sin beneficio.

**¿Por qué Supabase como punto de integración?**
Ya existe, ya tiene la estructura de datos, ya tiene Edge Functions útiles. Los agentes no necesitan una API custom — solo escriben a la misma DB que ya usa el CMS.

**¿Por qué HITL (Human in the Loop) obligatorio?**
Este es un sistema editorial personal. La voz de la marca es la voz del editor. Ningún sistema autónomo puede reemplazar ese criterio todavía. El HITL no es una limitación — es una feature. Con el tiempo, el Editor Agent aprende y el HITL se vuelve más liviano.

---

## Visión a futuro

### Fase 1 — MVP (actual)
Pipeline básico funcional: Scout → Writer → pending_review → aprobación humana → publicación manual.

### Fase 2 — Automatización completa
Publisher Agent activo. El humano aprueba y el sistema distribuye solo a todos los canales.

### Fase 3 — Loop de aprendizaje
Editor Agent que aprende de cada decisión humana y mejora sus criterios editoriales con el tiempo.

### Fase 4 — Sala de redacción visual
Interfaz de visualización en tiempo real del sistema trabajando. Estilo pixel art. Una ventana al trabajo de los agentes: quién está procesando qué, qué está en cola, qué se publicó. No solo métricas — una sala de redacción viva.

---

## Lo que este sistema nunca debe hacer

- Publicar sin aprobación humana
- Inventar datos o citar fuentes sin verificar
- Modificar posts que ya están publicados sin indicación explícita
- Acceder a datos fuera del scope de su tarea
- Ignorar un rechazo del editor humano sin registrarlo

---

*southsea-agents · The Southmetaverse Sea · Marzo 2026*
