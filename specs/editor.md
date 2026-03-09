# Spec: Editor Agent

## Rol
El Editor es el cuarto agente del pipeline editorial de The Southmetaverse Sea.
Su trabajo es evaluar la calidad de los borradores del Writer antes de que
lleguen al humano para aprobación final.

El Editor no genera contenido, no investiga, no publica.
Evalúa y toma una de dos decisiones: **aprobar** o **devolver**.
Nunca descarta un post.

---

## Input

Lee de la tabla `posts` con `status: pending_editing`.

Cada post contiene:
- `id` — UUID del post
- `title` — título en español
- `content` — contenido en español (markdown)
- `excerpt` — resumen para redes (max 280 chars)
- `tags` — clasificación temática
- `content_format` — formato usado (analysis|breaking|explainer|opinion)
- `analyst_brief_id` — referencia al brief de origen
- `revision_count` — número de veces que fue devuelto (default 0)

Para cada post, el Editor también lee el `analyst_brief` asociado
(via `analyst_brief_id`) para verificar alineación factual.

---

## Output

### Reviews

Escribe en la tabla `editor_reviews` via `agent-ingest`:

```python
{
    "table": "editor_reviews",
    "post_id": "uuid...",
    "decision": "approved" | "needs_revision",
    "scores": {
        "voice_alignment": 8.0,
        "factual_rigor": 7.5,
        "format_compliance": 9.0,
        "thematic_alignment": 8.5
    },
    "average_score": 8.25,
    "feedback": "...",
    "reviewer": "editor-agent",
    "human_note": null
}
```

### Actualizaciones al post

- **Aprobar**: actualiza post → `status: pending_review`
- **Devolver**: actualiza post → `status: needs_revision`, `revision_count: +1`

---

## Sistema editorial externo

El Editor carga los mismos recursos editoriales que el Writer:
- `editorial/voice.md` — para evaluar alineación con la voz de la marca
- `editorial/formats/` — para evaluar cumplimiento del formato

Reutiliza la lógica de `agents/writer/editorial_loader.py`.

---

## Modelo de IA

Usar Claude Haiku via `core/llm_client.py`.

Justificación: la evaluación editorial requiere análisis estructurado
pero no generación creativa. Haiku es suficiente para scoring + feedback.

Registrar en `core/model_config.py`:
```python
"editor.evaluator": "anthropic/claude-haiku-4-5-20251001",
```

---

## Evaluación: 4 dimensiones

El Editor evalúa cada post en 4 dimensiones, cada una con score de 1.0 a 10.0:

| Dimensión | Qué evalúa |
|-----------|------------|
| `voice_alignment` | ¿Respeta la voz editorial? Tono analítico, perspectiva propia, influencias Dalio/Harari/Balaji |
| `factual_rigor` | ¿Los datos coinciden con el brief? ¿Hay afirmaciones sin respaldo? |
| `format_compliance` | ¿Cumple la estructura del formato asignado? ¿Largo correcto? ¿Markdown bien formateado? |
| `thematic_alignment` | ¿El contenido es relevante para las temáticas de la marca? (Crypto/DeFi, Tech/IA, GenAI Art) |

### Regla de veto

Si **cualquier dimensión tiene score < 4.0**, el post se devuelve
sin importar el promedio. Esto garantiza un piso mínimo de calidad
en cada aspecto.

### Decisión

- Si todas las dimensiones ≥ 4.0 → **aprobar**
- Si alguna dimensión < 4.0 → **devolver** con feedback específico

---

## Regla de revision_count

Si un post tiene `revision_count >= 2`, el Editor lo aprueba automáticamente
con una nota especial para el humano:

```
human_note: "Post aprobado tras 2+ revisiones. Requiere atención editorial humana."
```

Esto evita loops infinitos entre Writer y Editor. El humano decide qué hacer.

---

## Flujo de ejecución

```
1. Al arrancar: cargar voice.md + todos los formatos de editorial/formats/
2. Leer posts con status: pending_editing (via agent-read)
3. Para cada post:
   a. Si revision_count >= 2 → aprobar con human_note (skip evaluación)
   b. Leer brief asociado (via agent-read con analyst_brief_id)
   c. Evaluar con Haiku: voice + formato + post + brief → 4 scores + feedback
   d. Aplicar regla de veto
   e. Si aprobado:
      - Guardar review en editor_reviews (via agent-ingest)
      - Actualizar post → status: pending_review (via agent-update)
   f. Si devuelto:
      - Guardar review con feedback en editor_reviews (via agent-ingest)
      - Actualizar post → status: needs_revision, revision_count +1 (via agent-update)
   g. Loguear: post evaluado, decisión, scores, feedback
4. Si un post falla, loguear error y continuar con el siguiente
```

---

## Manejo de errores

- Si `editorial/voice.md` no existe → error fatal, no arrancar
- Si `editorial/formats/` está vacío → error fatal, no arrancar
- Si la evaluación falla (LLM error) → loguear, no actualizar el post (reintento en próximo ciclo)
- Si el guardado de review falla → loguear, no actualizar el post
- Si el fetch del brief falla → evaluar sin brief (feedback lo menciona)
- Un post que falla no detiene el procesamiento de los demás

---

## Lo que el Editor NO hace

- No genera contenido (eso es del Writer)
- No recolecta fuentes (eso es del Scout)
- No investiga (eso es del Analyst)
- No descarta posts — solo aprueba o devuelve
- No publica en ningún canal (eso es del Publisher)
- No cambia el status a `published` — eso lo hace el humano
- No modifica el contenido del post — solo evalúa

---

## Estructura de archivos

```
agents/editor/
├── editor_agent.py       # orquestador principal
├── evaluator.py          # evaluación con Haiku (4 dimensiones + scoring)
├── editorial_loader.py   # reutiliza lógica del Writer
├── supabase_io.py        # lee posts/briefs, escribe reviews, actualiza posts
└── tests/
    ├── conftest.py
    ├── test_supabase_io.py
    ├── test_editorial_loader.py
    ├── test_evaluator.py
    └── test_editor_agent.py
```

---

## Tests obligatorios

### test_supabase_io.py
- Lee posts con status pending_editing correctamente
- Lee brief asociado por ID
- Guarda review con todos los campos requeridos
- Actualiza post a pending_review (aprobado)
- Actualiza post a needs_revision con revision_count incrementado (devuelto)

### test_editorial_loader.py
- Carga voice.md correctamente
- Carga formatos correctamente
- Error si voice.md no existe
- Error si formats/ vacío

### test_evaluator.py
- Dado un post + brief + voice + formato → retorna 4 scores + feedback + decision
- Si todas las dimensiones >= 4.0 → decision es "approved"
- Si alguna dimensión < 4.0 → decision es "needs_revision" (regla de veto)
- Feedback no está vacío cuando se devuelve
- Parseo correcto de respuesta JSON del LLM

### test_editor_agent.py
- Flujo completo: post → evaluación → review guardado → post actualizado
- Post aprobado → status pending_review
- Post devuelto → status needs_revision + revision_count incrementado
- Si revision_count >= 2 → auto-aprobado con human_note
- Si evaluación falla, el post NO se actualiza
- Cola vacía → ciclo termina sin errores
- Error en un post no detiene los demás

---

## Variables de entorno requeridas

```bash
# Ya configuradas (no agregar nuevas)
SUPABASE_URL=...
AGENTS_API_KEY=...
ANTHROPIC_API_KEY=...
```

---

*specs/editor.md · southsea-agents · Marzo 2026*
