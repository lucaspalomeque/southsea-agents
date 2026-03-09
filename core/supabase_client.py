import logging

import httpx

from core.config import SUPABASE_URL, AGENTS_API_KEY

logger = logging.getLogger(__name__)

INGEST_URL = f"{SUPABASE_URL}/functions/v1/agent-ingest"


def ingest_item(item: dict, table: str = "scout_items") -> dict:
    """Envía un item al Edge Function agent-ingest de Supabase.

    Args:
        item: Diccionario con los datos del item a ingestar.
        table: Nombre de la tabla destino.

    Returns:
        Respuesta del Edge Function como dict.

    Raises:
        httpx.HTTPStatusError: Si la respuesta tiene status >= 400.
    """
    body = {**item, "table": table}
    response = httpx.post(
        INGEST_URL,
        headers={
            "x-agent-key": AGENTS_API_KEY,
            "Content-Type": "application/json",
        },
        json=body,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    logger.info(f"Item ingestado en {table}: {item.get('title', '?')[:50]}")
    return data
