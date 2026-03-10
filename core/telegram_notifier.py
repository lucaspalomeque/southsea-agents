"""Notificador Telegram para el pipeline.

Envía el reporte de cada corrida al chat configurado.
Si las variables de entorno no están, no hace nada.
"""

import logging

import httpx

from core.config import SOUTHSEA_BOT_TOKEN, SOUTHSEA_CHAT_ID

logger = logging.getLogger(__name__)


def send_report(message: str) -> bool:
    """Envía un mensaje por Telegram. Retorna True si se envió, False si no."""
    if not SOUTHSEA_BOT_TOKEN or not SOUTHSEA_CHAT_ID:
        logger.info(
            "Telegram no configurado (SOUTHSEA_BOT_TOKEN/SOUTHSEA_CHAT_ID faltantes), "
            "saltando notificación"
        )
        return False

    try:
        url = f"https://api.telegram.org/bot{SOUTHSEA_BOT_TOKEN}/sendMessage"
        response = httpx.post(
            url,
            json={"chat_id": SOUTHSEA_CHAT_ID, "text": message},
            timeout=15,
        )
        response.raise_for_status()
        logger.info("Reporte enviado por Telegram")
        return True
    except Exception as e:
        logger.error(f"Error enviando reporte por Telegram: {e}")
        return False
