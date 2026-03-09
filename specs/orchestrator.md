# Spec: Pipeline Orchestrator

## Referencia
Sesión #5 — southsea-agents
Fecha: 9 de marzo de 2026

---

## Qué es

El orquestador es un script Python que ejecuta los 4 agentes del pipeline editorial en secuencia:

```
Scout → Analyst → Writer → Editor
```

Es el "jefe de turno" de la redacción. No escribe notas, no investiga, no redacta, no corrige. Solo sabe el orden, da la señal de arranque a cada agente, controla que no se traben, y al final deja un reporte.

---

## Archivo

```
scripts/run_pipeline.py
```

Ejecutable con:
```bash
cd southsea-agents
python scripts/run_pipeline.py
```

---

## Flujo de ejecución

```
1. Iniciar logging (archivo + consola)
2. Registrar timestamp de inicio
3. Ejecutar Scout Agent
   → Capturar: items_found, items_saved, errors
   → Si falla completamente: loguear, continuar al paso 4
4. Ejecutar Analyst Agent
   → Lee scout_items con status: pending_analysis
   → Timeout: 5 minutos por item individual
   → Si un item se traba: skip ese item, loguear, seguir con el siguiente
   → Si no hay items nuevos: loguear "nada que analizar", continuar
   → Capturar: items_processed, items_skipped, errors
5. Ejecutar Writer Agent
   → Lee analyst_briefs con status: pending_writing
   → Timeout: 5 minutos por brief individual
   → Si un brief se traba: skip, loguear, seguir
   → Si no hay briefs nuevos: loguear "nada que escribir", continuar
   → Capturar: posts_created, posts_skipped, errors
6. Ejecutar Editor Agent
   → Lee posts con status: pending_editing
   → Timeout: 5 minutos por post individual
   → Si un post se traba: skip, loguear, seguir
   → Si no hay posts nuevos: loguear "nada que editar", continuar
   → Capturar: posts_approved, posts_returned, errors
7. Generar reporte final
8. Registrar timestamp de fin
9. Escribir reporte a log
```

---

## Manejo de errores

### Principio: un agente que falla no tumba el pipeline

Si el Scout crashea, el Analyst igual corre — puede que haya items de una corrida anterior esperando. Lo mismo para cada agente subsiguiente.

### Timeout por item

- **5 minutos** por item/brief/post individual
- Si se excede: marcar como `error_timeout` (no cambiar status en DB), loguear, continuar con el siguiente
- El timeout aplica a la llamada LLM, no al agente completo
- Implementación: `asyncio.wait_for()` o `signal.alarm()` (preferir asyncio si los agentes ya son async, signal si son sync)

### Errores de red / API

- Retry 1 vez con backoff de 30 segundos
- Si falla el retry: skip item, loguear error completo (traceback)
- Nunca retry infinito

### Pipeline vacío

No es un error. Si el Scout no encuentra nada nuevo → el Analyst no tiene trabajo → el Writer no tiene trabajo → el Editor no tiene trabajo. El reporte final dice "pipeline vacío, todo al día" y termina normalmente.

---

## Logging

### Destinos
1. **Archivo**: `logs/pipeline_YYYY-MM-DD_HH-MM-SS.log`
2. **Consola**: stdout (para cuando se corre manualmente)

### Formato
```
[2026-03-09 12:00:05] [INFO] [orchestrator] Pipeline iniciado
[2026-03-09 12:00:06] [INFO] [scout] Iniciando ciclo...
[2026-03-09 12:00:15] [INFO] [scout] CoinDesk: 5 items nuevos
[2026-03-09 12:00:16] [WARNING] [scout] Bankless: SSL error, skipping
[2026-03-09 12:01:30] [INFO] [scout] Ciclo completo: 8 items guardados
[2026-03-09 12:01:31] [INFO] [analyst] Iniciando análisis de 8 items...
[2026-03-09 12:03:45] [ERROR] [analyst] Item abc123: timeout después de 5 min, skipping
...
[2026-03-09 12:15:00] [INFO] [orchestrator] Pipeline completo en 15m 00s
```

### Retención de logs
- Mantener los últimos 30 archivos de log
- Cada corrida = 1 archivo
- Rotación simple: si hay más de 30, borrar el más viejo

---

## Reporte final

Al terminar cada corrida, el orquestador genera un resumen:

```
═══════════════════════════════════════════
  PIPELINE REPORT — 2026-03-09 12:00 UTC
═══════════════════════════════════════════

  Scout:    8 found → 6 saved, 2 duplicates, 0 errors
  Analyst:  6 items → 5 processed, 1 timeout, 0 errors
  Writer:   5 briefs → 5 posts created, 0 skipped
  Editor:   5 posts → 4 approved, 1 needs_revision

  Duration: 14m 32s
  Status:   ✅ OK (4 posts ready for review)

═══════════════════════════════════════════
```

Este reporte va al log Y a la consola.

---

## Cron job

### Setup temporal (Mac, hasta migrar a VPS)

```bash
# Editar crontab
crontab -e

# Agregar línea (cada 6 horas)
0 0,6,12,18 * * * cd /path/to/southsea-agents && /path/to/.venv/bin/python scripts/run_pipeline.py >> logs/cron.log 2>&1
```

### Setup definitivo (VPS Linux, sesión 6)
Se migrará a systemd timer o cron del servidor. El script no cambia — solo cambia quién lo invoca.

---

## Estructura de archivos nuevos

```
southsea-agents/
├── scripts/
│   └── run_pipeline.py      # el orquestador
├── logs/                     # directorio de logs (en .gitignore)
│   └── .gitkeep
```

### Agregar a .gitignore
```
logs/*.log
```

---

## Interfaz con cada agente

El orquestador necesita que cada agente exponga una función ejecutable que devuelva resultados. Patrón:

```python
# Lo que el orquestador espera de cada agente
class AgentResult:
    agent_name: str
    items_input: int       # cuántos items recibió
    items_success: int     # cuántos procesó OK
    items_skipped: int     # cuántos skippeó (timeout, error)
    items_error: int       # cuántos fallaron
    errors: list[str]      # mensajes de error
    duration_seconds: float

# Cada agente debe tener:
def run() -> AgentResult:
    ...
```

Si los agentes actuales no devuelven este formato, el orquestador los wrappea con adaptadores.

---

## Lo que NO hace el orquestador

- No toca la base de datos directamente (eso lo hacen los agentes)
- No modifica el status de items que no procesó
- No decide si un post es bueno o malo
- No reintenta items que ya falló un agente (eso es para la siguiente corrida)
- No envía notificaciones (eso va en sesión 6 con el VPS + Telegram)

---

## Tests

- `test_orchestrator.py`:
  - Pipeline completo con mocks de los 4 agentes → reporte correcto
  - Scout falla → los otros 3 igual corren
  - Analyst timeout en 1 item → ese item se skipea, los demás se procesan
  - Pipeline vacío (0 items) → termina OK sin errores
  - Log file se crea en `logs/`

---

## Preguntas resueltas

| Pregunta | Decisión |
|----------|----------|
| ¿Qué si el Scout no encuentra items? | Pipeline vacío, OK, sin error |
| ¿Timeout por agente? | 5 min por item individual, skip y seguir |
| ¿Notificación? | Solo logs por ahora, Telegram en VPS |
| ¿Dónde corre? | Mac temporal, VPS en sesión 6 |
| ¿Retry? | 1 retry con 30s backoff, después skip |

---

*specs/orchestrator.md · southsea-agents · Sesión 5 · 9 de marzo de 2026*