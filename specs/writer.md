# Spec: Writer Agent

## Rol
El Writer es el tercer agente del pipeline editorial de The Southmetaverse Sea.
Su trabajo es transformar los briefs del Analyst en artículos editoriales
con la voz de la marca.

El Writer no recolecta fuentes, no investiga, no verifica datos.
Recibe un brief verificado y produce un borrador listo para revisión editorial.

---

## Input

Lee de la tabla `analyst_briefs` con `status: pending_writing`.

Cada brief contiene:
- `title` — título de trabajo (puede cambiar)
- `context` — contexto investigado por el Analyst
- `key_entities` — entidades relevantes (JSON)
- `editorial_angle` — ángulo sugerido por el Analyst
- `verified_facts` — datos verificados (array de strings)
- `research_notes` — notas adicionales de investigación

El Writer usa todo esto como materia prima. No es un dictado —
es un brief de redacción que el Writer interpreta con criterio editorial.

---

## Output

Escribe en la tabla `posts` con estos campos:

```python
{
    "title": "...",                    # título en español
    "content": "...",                  # contenido en español (markdown)
    "excerpt": "...",                  # resumen para redes (max 280 chars, español)
    "tags": ["crypto_defi", ...],      # heredados del brief / scout_item
    "content_format": "analysis",      # qué formato usó (analysis|explainer|opinion|breaking)
    "status": "pending_review",        # SIEMPRE pending_review
    "created_by": "writer-agent",      # identificar origen
    "original_language": "es",         # siempre español en MVP
    "analyst_brief_id": "uuid..."      # referencia al brief de origen
}
```

Después de guardar el post, el Writer:
1. Invoca la Edge Function `translate-post` para generar la versión en inglés
2. Actualiza el brief en `analyst_briefs` → `status: processed`

### Estrategia bilingüe (MVP)

Generar en español. Traducir con `translate-post`.

Justificación: la voz editorial se diseñó pensando en español.
La Edge Function de traducción ya existe y funciona.
En una fase posterior se puede migrar a generación dual si la
calidad de la traducción no es suficiente.

---

## Sistema editorial externo

La voz y los formatos de contenido NO viven en el código del Writer.
Viven en archivos markdown que el Writer lee al ejecutarse:

```
editorial/
├── voice.md              # manual de estilo de la marca
└── formats/
    ├── analysis.md       # artículo de análisis (600-1200 palabras)
    ├── explainer.md      # explainer corto (300-600 palabras)
    ├── opinion.md        # pieza de opinión (400-800 palabras)
    └── breaking.md       # noticia urgente (200-400 palabras)
```

### Por qué está separado

El editor jefe (el humano) puede modificar la voz y los formatos
sin tocar código Python. Editar `voice.md` es como actualizar el
manual de estilo de una redacción — los periodistas (agentes)
consultan el manual antes de escribir, pero el manual lo controla
el editor.

Esto permite:
- Iterar el tono sin hacer deploy
- Agregar nuevos formatos sin modificar el Writer
- Versionar los cambios editoriales en git
- Testear una voz diferente sin riesgo

### Cómo los consume el Writer

Al arrancar, el Writer:
1. Lee `editorial/voice.md` → lo inyecta en el system prompt
2. Lee todos los archivos de `editorial/formats/` → los carga como opciones
3. Para cada brief, elige el formato más adecuado
4. Construye el prompt combinando: voice + formato elegido + brief

---

## Selección de formato

El Writer decide qué formato usar según el contenido del brief.
La lógica de selección:

| Señal en el brief | Formato |
|-------------------|---------|
| Evento reciente + pocos datos verificados + urgencia | `breaking` |
| Entidad nueva + needs_research fue true | `explainer` |
| Ángulo editorial polémico + tema regulación/geopolítica | `opinion` |
| Default: análisis con contexto y datos suficientes | `analysis` |

Esta lógica se implementa como una función pura en `format_selector.py`.
Puede usar heurísticas simples (keywords, largo del brief, campos presentes)
o una llamada a Haiku para clasificar. Empezar con heurísticas simples.

Si en el futuro se agregan más formatos, solo hay que:
1. Crear el archivo `.md` en `editorial/formats/`
2. Agregar la señal de selección en `format_selector.py`

---

## Excerpt

Resumen para redes sociales. Máximo 280 caracteres.
Debe funcionar como tweet independiente: capturar la esencia
del artículo y generar curiosidad sin ser clickbait.

Se genera en la misma llamada al LLM que el artículo.

---

## Modelo de IA

Usar Claude Sonnet via `core/llm_client.py`.

Justificación: el Writer necesita capacidad creativa y coherencia
de largo aliento. Haiku es demasiado superficial para prosa editorial.
Opus es innecesario para borradores que serán revisados por Editor + humano.

Registrar en `core/model_config.py`:
```python
"writer.content_generator": "anthropic/claude-sonnet-4-20250514",
```

---

## Flujo de ejecución

```
1. Al arrancar: cargar voice.md + todos los formatos de editorial/formats/
2. Leer briefs con status: pending_writing (via agent-read)
3. Para cada brief:
   a. Seleccionar formato (format_selector)
   b. Construir prompt: voice + formato seleccionado + brief
   c. Llamar a Claude Sonnet → generar artículo en español
   d. Extraer: título, contenido (markdown), excerpt, formato usado
   e. Guardar en tabla posts (via agent-ingest) → status: pending_review
   f. Invocar translate-post para generar versión en inglés
   g. Actualizar brief → status: processed (via agent-update)
   h. Loguear: brief procesado, post creado, formato usado, traducción solicitada
4. Si un brief falla, loguear error y continuar con el siguiente
```

---

## Manejo de errores

- Si `editorial/voice.md` no existe → error fatal, no arrancar
- Si `editorial/formats/` está vacío → error fatal, no arrancar
- Si la generación de contenido falla → loguear, no actualizar el brief (reintento en próximo ciclo)
- Si el guardado en posts falla → loguear, no actualizar el brief
- Si translate-post falla → loguear warning pero SÍ actualizar el brief (el post existe, la traducción se puede reintentar)
- Un brief que falla no detiene el procesamiento de los demás

---

## Lo que el Writer NO hace

- No recolecta fuentes (eso es del Scout)
- No investiga entidades (eso es del Analyst)
- No modifica posts existentes — solo crea nuevos
- No publica en ningún canal (eso es del Publisher)
- No cambia el status a `published` — eso lo hace el humano
- No genera contenido en inglés directamente — delega a translate-post
- No genera imágenes ni contenido multimedia (futura iteración)
- No define la voz editorial — la lee de `editorial/voice.md`
- No define los formatos — los lee de `editorial/formats/`

---

## Tabla de referencia: `posts`

Los campos que el Writer escribe:

| Campo | Tipo | Requerido | Quién lo escribe |
|-------|------|-----------|------------------|
| title | text | ✅ | Writer (español) |
| content | text | ✅ | Writer (español, markdown) |
| excerpt | text | ✅ | Writer (español, max 280 chars) |
| tags | text[] | ✅ | Writer (heredados del brief) |
| content_format | text | ✅ | Writer (analysis/explainer/opinion/breaking) |
| status | text | ✅ | Writer → `pending_review` |
| created_by | text | ✅ | Writer → `writer-agent` |
| original_language | text | ✅ | Writer → `es` |
| analyst_brief_id | uuid | ✅ | Writer (referencia al brief) |
| title_en | text | ○ | translate-post (Edge Function) |
| content_en | text | ○ | translate-post |
| excerpt_en | text | ○ | translate-post |

Nota: los campos `_en` los llena la Edge Function, no el Writer.
Verificar que el schema de `posts` tiene estos campos antes de implementar.

---

## Estructura de archivos

```
agents/writer/
├── writer_agent.py        # orquestador principal (carga editorial, lee briefs, coordina)
├── content_generator.py   # genera artículo con Claude Sonnet
├── format_selector.py     # elige formato según el brief
├── editorial_loader.py    # carga voice.md + formatos al arrancar
├── supabase_io.py         # lee briefs (agent-read), escribe posts (agent-ingest)
├── translator.py          # invoca Edge Function translate-post
└── tests/
    ├── test_content_generator.py
    ├── test_format_selector.py
    ├── test_editorial_loader.py
    ├── test_supabase_io.py
    └── test_writer_agent.py

editorial/                   # ← en la raíz del repo, NO dentro de agents/
├── voice.md
└── formats/
    ├── analysis.md
    ├── explainer.md
    ├── opinion.md
    └── breaking.md
```

---

## Tests obligatorios

### test_content_generator.py
- Dado un brief sintético + voice + formato, genera artículo con título, contenido y excerpt
- El contenido respeta el rango de palabras del formato seleccionado
- El excerpt tiene máximo 280 caracteres
- El contenido está en formato markdown con al menos 2 secciones (##)

### test_format_selector.py
- Brief con evento reciente y pocos datos → selecciona `breaking`
- Brief con entidad desconocida investigada → selecciona `explainer`
- Brief con ángulo polémico sobre regulación → selecciona `opinion`
- Brief genérico con contexto completo → selecciona `analysis`

### test_editorial_loader.py
- Carga voice.md correctamente como string
- Carga todos los formatos de editorial/formats/
- Error fatal si voice.md no existe
- Error fatal si formats/ está vacío

### test_supabase_io.py
- Lee briefs con status pending_writing correctamente
- Guarda post con todos los campos requeridos incluyendo content_format
- Actualiza brief a status processed

### test_writer_agent.py
- Flujo completo: brief → formato seleccionado → artículo → post guardado → brief actualizado
- Si la generación falla, el brief NO se actualiza
- Si el guardado falla, el brief NO se actualiza
- Si translate-post falla, el brief SÍ se actualiza (warning)
- El campo content_format del post coincide con el formato seleccionado

---

## Variables de entorno requeridas

```bash
# Ya configuradas (no agregar nuevas)
SUPABASE_URL=...
AGENTS_API_KEY=...
ANTHROPIC_API_KEY=...
```

No se necesitan variables nuevas. El Writer usa la misma infraestructura
que el Scout y el Analyst.

---

## Frecuencia de ejecución

Por ahora: manual. Se corre cuando hay briefs pendientes.

Futuro: cron job coordinado con el pipeline completo
(después de que el Scout y Analyst hayan corrido su ciclo).

---

*specs/writer.md · southsea-agents · Marzo 2026*