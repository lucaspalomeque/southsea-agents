"""Invoca la Edge Function translate-post para generar versión en inglés.

La traducción es best-effort: si falla, el post en español ya existe
y la traducción se puede reintentar después.
"""

import logging

import httpx

from core.config import SUPABASE_URL, AGENTS_API_KEY

logger = logging.getLogger(__name__)

TRANSLATE_URL = f"{SUPABASE_URL}/functions/v1/translate-post"

HEADERS = {
    "x-agent-key": AGENTS_API_KEY,
    "Content-Type": "application/json",
}
TIMEOUT = 60  # traducción puede tardar más


def translate_post(post_id: str) -> bool:
    """Invoca translate-post para generar la versión en inglés.

    Returns:
        True si la traducción fue exitosa, False si falló.
        No lanza excepciones — loguea el error como warning.
    """
    try:
        response = httpx.post(
            TRANSLATE_URL,
            headers=HEADERS,
            json={"post_id": post_id},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        logger.info(f"Traducción solicitada para post {post_id}")
        return True
    except Exception as e:
        logger.warning(f"Traducción falló para post {post_id}: {e}")
        return False
