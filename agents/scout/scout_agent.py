import logging
from datetime import datetime, timezone

from agents.scout.sources.rss import fetch_all_feeds
from agents.scout.classifier import classify_items
from agents.scout.deduplicator import deduplicate
from core.supabase_client import ingest_item

logger = logging.getLogger(__name__)


class ScoutAgent:
    """Monitorea fuentes RSS y recolecta items relevantes.
    Ver specs/scout.md para el detalle completo.
    """

    def __init__(self):
        self.seen_urls: set[str] = set()

    def run(self) -> list[dict]:
        """Ejecuta un ciclo completo de recoleccion."""
        start = datetime.now(timezone.utc)
        logger.info(f"[{start.isoformat()}] Scout iniciando ciclo")

        # 1. Fetch
        raw_items = fetch_all_feeds()
        logger.info(f"Items crudos obtenidos: {len(raw_items)}")

        if not raw_items:
            logger.info("No se encontraron items nuevos. Ciclo terminado.")
            return []

        # 2. Clasificar
        try:
            classified = classify_items(raw_items)
        except Exception as e:
            logger.error(f"Error en clasificacion: {e}")
            return []

        logger.info(f"Items clasificados: {len(classified)}")

        # 3. Deduplicar
        unique = deduplicate(classified, self.seen_urls)
        logger.info(f"Items unicos: {len(unique)}")

        # 4. Enviar a Supabase
        ingested = []
        for item in unique:
            try:
                result = ingest_item(item)
                ingested.append(result)
            except Exception as e:
                logger.error(f"Error ingesting item '{item.get('title', '?')}': {e}")
                continue

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        logger.info(
            f"Scout ciclo completado en {elapsed:.1f}s — "
            f"crudos: {len(raw_items)}, clasificados: {len(classified)}, "
            f"unicos: {len(unique)}, enviados: {len(ingested)}"
        )
        return ingested
