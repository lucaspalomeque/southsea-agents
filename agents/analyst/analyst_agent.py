"""Analyst Agent — segundo agente del pipeline editorial.

Lee scout_items pendientes, investiga entidades desconocidas,
produce briefs estructurados para el Writer, y actualiza status.

Pipeline por item:
1. Marcar scout_item como in_analysis
2. Si needs_research → investigar entidades con Claude Sonnet
3. Construir brief estructurado
4. Guardar brief en analyst_briefs
5. Marcar scout_item como processed
"""

import logging
from datetime import datetime, timezone

from agents.analyst.supabase_io import fetch_pending_items, update_scout_item, save_brief
from agents.analyst.researcher import research_entities
from agents.analyst.brief_builder import build_brief

logger = logging.getLogger(__name__)


class AnalystAgent:
    """Analiza scout_items y produce briefs para el Writer."""

    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size

    def run(self) -> list[dict]:
        """Ejecuta un ciclo de analisis."""
        start = datetime.now(timezone.utc)
        logger.info(f"[{start.isoformat()}] Analyst iniciando ciclo")

        items = fetch_pending_items(limit=self.batch_size)
        if not items:
            logger.info("No hay items pendientes. Ciclo terminado.")
            return []

        logger.info(f"Items a procesar: {len(items)}")

        briefs = []
        errors = 0
        for item in items:
            try:
                brief = self._process_item(item)
                briefs.append(brief)
            except Exception as e:
                errors += 1
                item_id = item.get("id", "?")
                logger.error(f"Error procesando item {item_id}: {e}")
                try:
                    update_scout_item(item_id, {"status": "pending_analysis"})
                except Exception as rollback_err:
                    logger.error(f"Error restaurando status de {item_id}: {rollback_err}")
                continue

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        logger.info(
            f"Analyst ciclo completado en {elapsed:.1f}s — "
            f"procesados: {len(briefs)}, errores: {errors}"
        )
        return briefs

    def _process_item(self, item: dict) -> dict:
        """Procesa un solo scout_item: research → brief → save."""
        item_id = item["id"]
        title = item.get("title", "?")
        logger.info(f"Procesando: {title} ({item_id})")

        # 1. Marcar como in_analysis
        update_scout_item(item_id, {"status": "in_analysis"})

        # 2. Investigar si es necesario
        research = {}
        if item.get("needs_research"):
            logger.info(f"  Investigando entidades: {item.get('needs_research_reason', '')}")
            research = research_entities(item)

        # 3. Construir brief
        brief_data = build_brief(item, research)

        # 4. Guardar brief en Supabase
        saved = save_brief(brief_data)

        # 5. Marcar scout_item como processed
        update_scout_item(item_id, {"status": "processed"})

        logger.info(f"  Brief creado para: {title}")
        return saved
