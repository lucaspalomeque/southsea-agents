# ROADMAP.md — southsea-agents

> Plan de construcción del sistema editorial autónomo de The Southmetaverse Sea.
> Documento vivo — se actualiza al final de cada sesión de trabajo.
> Última actualización: 4 de marzo de 2026

---

## Estado actual

```
✅ ARCHITECTURE.md — diseño completo del sistema
✅ CLAUDE.md — instrucciones para agentes
✅ specs/scout.md — spec completa del Scout Agent
✅ Repo creado y pusheado a GitHub
✅ Estructura de carpetas base

⏳ Migración de DB — pending_review + created_by + scout_items
⏳ Scout Agent — primer agente funcional
⏳ Resto del pipeline — Analyst, Writer, Editor, Publisher
```

---

## Fase 1 — Cimientos (Esta semana)

### 1.1 Push de documentación al repo
**Estado:** Pendiente
**Tiempo estimado:** 5 minutos
**Tareas:**
- [ ] Push de ARCHITECTURE.md
- [ ] Push de CLAUDE.md
- [ ] Push de specs/scout.md
- [ ] Push de ROADMAP.md (este archivo)

---

### 1.2 Migración de base de datos
**Estado:** Pendiente
**Tiempo estimado:** 15 minutos
**Repo:** southmetaverse-sea (CMS)
**Tareas:**
- [ ] Agregar estado `pending_review` al campo `status` de la tabla `posts`
- [ ] Agregar campo `created_by text` a la tabla `posts`
- [ ] Crear tabla nueva `scout_items` (ver schema en specs/scout.md)
- [ ] Verificar que el CMS sigue funcionando después de la migración

**Por qué es prioritario:** Sin estos cambios, los agentes no tienen dónde escribir.

---

### 1.3 Scout Agent — MVP
**Estado:** Pendiente
**Tiempo estimado:** 2-3 sesiones de trabajo
**Método:** Worktree + Claude Code ejecutando specs/scout.md

**Preparación:**
- [ ] Crear worktree: `git worktree add ../southsea-agents-scout feature/scout-agent`
- [ ] Abrir Claude Code en el worktree
- [ ] Configurar `.env` con credenciales de Supabase y Telegram

**Construcción (Claude Code ejecuta la spec):**
- [ ] `core/supabase_client.py` — cliente Supabase compartido
- [ ] `core/models.py` — modelos de datos (ScoutItem, etc.)
- [ ] `core/config.py` — configuración desde .env
- [ ] `agents/scout/sources/rss.py` — parser RSS (CoinDesk, Bankless, Coin Bureau, YouTube)
- [ ] `agents/scout/sources/telegram.py` — cliente Telegram + script get_telegram_ids.py
- [ ] `agents/scout/sources/binance.py` — anuncios de Binance
- [ ] `agents/scout/classifier.py` — clasificación temática
- [ ] `agents/scout/deduplicator.py` — lógica de deduplicación
- [ ] `agents/scout/scout_agent.py` — clase principal
- [ ] `agents/scout/tests/` — tests con datos sintéticos

**Validación:**
- [ ] Tests pasan en verde
- [ ] Scout corre manualmente sin errores
- [ ] Items aparecen en Supabase con `status: pending_analysis`
- [ ] Logs claros y trazables

**Cierre:**
- [ ] Merge del worktree al main
- [ ] Push a GitHub
- [ ] Worktree eliminado

---

### 1.4 Configuración de fuentes Telegram
**Estado:** Pendiente
**Tiempo estimado:** 30 minutos
**Tareas:**
- [ ] Correr `scripts/get_telegram_ids.py` para obtener IDs de:
  - y22 trades
  - crypto goodreads
  - crypto narratives
- [ ] Agregar IDs al `.env`
- [ ] Verificar que el Scout lee mensajes de los 3 canales

---

## Fase 2 — Pipeline completo (Semanas 2-3)

### 2.1 Analyst Agent
**Estado:** Pendiente — spec no escrita todavía
**Tareas previas:**
- [ ] Escribir specs/analyst.md
- [ ] Revisar y aprobar spec
**Construcción:**
- [ ] Crear worktree: `feature/analyst-agent`
- [ ] Claude Code ejecuta la spec
- [ ] Verificar que lee de `scout_items` y produce briefs
- [ ] Merge y push

**Rol:** Toma items del Scout, investiga entidades desconocidas, verifica datos, arma brief estructurado para el Writer.

---

### 2.2 Writer Agent
**Estado:** Pendiente — spec no escrita todavía
**Tareas previas:**
- [ ] Escribir specs/writer.md (incluye definición detallada de voz editorial)
- [ ] Definir ejemplos de voz: cómo suena bien vs cómo suena mal
- [ ] Revisar y aprobar spec
**Construcción:**
- [ ] Crear worktree: `feature/writer-agent`
- [ ] Claude Code ejecuta la spec
- [ ] Verificar que genera borradores con la voz correcta
- [ ] Merge y push

**Voz editorial:** Techno-optimista + estilo Harari + metáforas Borges + d/acc + The Network State

---

### 2.3 Editor Agent
**Estado:** Pendiente — spec no escrita todavía
**Tareas previas:**
- [ ] Escribir specs/editor.md
- [ ] Definir criterios de calidad editorial
- [ ] Revisar y aprobar spec
**Construcción:**
- [ ] Crear worktree: `feature/editor-agent`
- [ ] Claude Code ejecuta la spec
- [ ] Verificar que filtra correctamente antes de pending_review
- [ ] Merge y push

**Rol:** Revisa borradores del Writer. Aprueba o devuelve con comentarios. Aprende de las decisiones del editor humano.

---

### 2.4 Cola de aprobación en el CMS
**Estado:** Pendiente
**Repo:** southmetaverse-sea (CMS)
**Tareas:**
- [ ] Crear vista en el dashboard para posts con `status: pending_review`
- [ ] Botón de aprobar → cambia status a `published`
- [ ] Botón de rechazar → elimina o devuelve al pipeline con comentario
- [ ] Mostrar campo `created_by` para identificar origen (agente o humano)

**Por qué es crítico:** Sin esto, el humano no puede aprobar el contenido generado por agentes.

---

### 2.5 Pipeline end-to-end — primera prueba real
**Estado:** Pendiente
**Objetivo:** Una noticia real recorre todo el pipeline y llega al dashboard para aprobación.

```
Scout recolecta → Analyst procesa → Writer genera borrador
→ Editor revisa → pending_review en Supabase
→ Humano aprueba desde el dashboard del CMS
```

- [ ] Correr pipeline completo manualmente
- [ ] Verificar cada paso con logs
- [ ] Aprobar el primer borrador generado por agentes
- [ ] Celebrar 🎉

---

## Fase 3 — Distribución automática (Semana 4)

### 3.1 Publisher Agent
**Estado:** Pendiente — spec no escrita todavía
**Tareas previas:**
- [ ] Escribir specs/publisher.md
- [ ] Conseguir API keys de canales de distribución
- [ ] Revisar y aprobar spec

**Canales a integrar:**
- [ ] Blog (southmetaverse-sea — ya existe, publicación automática via Supabase)
- [ ] Substack — API o integración
- [ ] Moltbook — API o integración
- [ ] X / Twitter — requiere plan Basic $200/mes (evaluar cuando el sistema esté probado)

---

### 3.2 Cron job — ejecución automática cada 6 horas
**Estado:** Pendiente
**Tareas:**
- [ ] Configurar scheduler (cron local o servicio cloud)
- [ ] Scout corre automáticamente 00:00 / 06:00 / 12:00 / 18:00 UTC
- [ ] Alertas si algún ciclo falla
- [ ] Logs persistentes por ciclo

---

## Fase 4 — Loop de aprendizaje (Semana 5-6)

### 4.1 Sistema de feedback editorial
**Estado:** Pendiente
**Objetivo:** Cada decisión del editor humano (aprobar/rechazar/editar) alimenta la memoria del sistema.

**Tareas:**
- [ ] Registrar decisiones del editor en tabla `editorial_feedback`
- [ ] Editor Agent lee el historial de feedback antes de revisar nuevos borradores
- [ ] Después de 10+ decisiones, el Editor Agent ajusta sus criterios automáticamente
- [ ] Revisar periódicamente que los criterios aprendidos son correctos

---

### 4.2 Métricas de performance
**Estado:** Pendiente
**Tareas:**
- [ ] Tasa de aprobación por agente (qué % de borradores aprueba el humano)
- [ ] Tasa de rechazo por motivo (voz incorrecta, datos no verificados, fuera de temática)
- [ ] Items procesados por ciclo por fuente
- [ ] Dashboard simple de métricas en el CMS

---

## Fase 5 — Sala de redacción visual (Futuro)

### 5.1 Visualización en tiempo real
**Estado:** Idea — diseño pendiente
**Concepto:** Interfaz visual que muestra los agentes trabajando en tiempo real. Estilo pixel art. Una ventana al sistema — no solo métricas, una sala de redacción viva.

**Elementos a visualizar:**
- [ ] Estado de cada agente (idle, working, waiting)
- [ ] Items en cola por etapa del pipeline
- [ ] Últimas noticias procesadas
- [ ] Últimos borradores generados
- [ ] Historial de publicaciones

**Nota:** Esta fase empieza solo cuando el motor (Fases 1-4) esté funcionando de forma estable.

---

## Fuentes pendientes de configurar

| Fuente | Estado | Bloqueante |
|--------|--------|-----------|
| Telegram — y22 trades | Pendiente ID | Correr get_telegram_ids.py |
| Telegram — crypto goodreads | Pendiente ID | Correr get_telegram_ids.py |
| Telegram — crypto narratives | Pendiente ID | Correr get_telegram_ids.py |
| Nansen | Pendiente API key | Evaluar plan de precios |
| X / Twitter — todas las cuentas | Fase 2 | API Basic $200/mes |
| Higgsfield | Pendiente confirmar canal | Verificar si tiene Telegram o solo X |
| 0xSamm | Pendiente confirmar handle | Verificar handle exacto en X |

---

## Decisiones pendientes

- [ ] **Hosting del sistema de agentes:** ¿corre en tu Mac 24/7 o migramos a un VPS? Evaluar cuando el pipeline esté estable.
- [ ] **Nansen API:** ¿el valor justifica el costo? Evaluar en Fase 2.
- [ ] **X / Twitter:** ¿$200/mes tiene sentido cuando el sistema esté probado? Evaluar en Fase 3.
- [ ] **Substack + Moltbook APIs:** Investigar disponibilidad y costo de integración.

---

## Principio de trabajo

```
Spec primero → worktree → Claude Code ejecuta → revisión humana → merge
```

Nunca escribir código sin spec aprobada.
Nunca mergear sin que los tests pasen.
Nunca publicar sin aprobación humana.

---

*southsea-agents · The Southmetaverse Sea · Marzo 2026*
*Roadmap vivo — actualizar al final de cada sesión*
