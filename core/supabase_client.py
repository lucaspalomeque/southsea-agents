import logging

import httpx

from core.config import SUPABASE_URL, AGENTS_API_KEY

logger = logging.getLogger(__name__)

INGEST_URL = f"{SUPABASE_URL}/functions/v1/agent-ingest"


def ingest_item(item: dict) -> dict:
    """Envía un item al Edge Function agent-ingest de Supabase.

    Args:
        item: Diccionario con los datos del item a ingestar.

    Returns:
        Respuesta del Edge Function como dict.

    Raises:
        httpx.HTTPStatusError: Si la respuesta tiene status >= 400.
    """
    response = httpx.post(
        INGEST_URL,
        headers={
            "Authorization": f"Bearer {AGENTS_API_KEY}",
            "Content-Type": "application/json",
        },
        json=item,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    logger.info(f"Item ingestado: {data}")
    return data
