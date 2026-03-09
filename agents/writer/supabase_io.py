"""Comunicación con Supabase via Edge Functions para el Writer Agent.

Endpoints:
- agent-read:   POST {table, filters, limit} → {success, data, count}
- agent-ingest:  POST {table, ...campos}     → {success, data}
- agent-update:  POST {table, id, updates}   → {success, data}

Todos autenticados con x-agent-key.
"""

import logging

import httpx

from core.config import SUPABASE_URL, AGENTS_API_KEY

logger = logging.getLogger(__name__)

READ_URL = f"{SUPABASE_URL}/functions/v1/agent-read"
INGEST_URL = f"{SUPABASE_URL}/functions/v1/agent-ingest"
UPDATE_URL = f"{SUPABASE_URL}/functions/v1/agent-update"

HEADERS = {
    "x-agent-key": AGENTS_API_KEY,
    "Content-Type": "application/json",
}
TIMEOUT = 30


def fetch_pending_briefs(limit: int = 10) -> list[dict]:
    """Lee analyst_briefs con status=pending_writing."""
    response = httpx.post(
        READ_URL,
        headers=HEADERS,
        json={
            "table": "analyst_briefs",
            "filters": {"status": "pending_writing"},
            "limit": limit,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    items = result.get("data", [])
    logger.info(f"Fetched {len(items)} pending briefs")
    return items


def save_post(post: dict) -> dict:
    """Guarda un post en Supabase via agent-ingest.

    agent-ingest espera campos flat con 'table' como campo adicional.
    """
    body = {**post, "table": "posts"}
    response = httpx.post(
        INGEST_URL,
        headers=HEADERS,
        json=body,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    logger.info(f"Post guardado: {post.get('title', '?')[:50]}")
    return result.get("data", result)


def update_brief_status(brief_id: str, status: str) -> dict:
    """Actualiza el status de un analyst_brief."""
    response = httpx.post(
        UPDATE_URL,
        headers=HEADERS,
        json={
            "table": "analyst_briefs",
            "id": brief_id,
            "updates": {"status": status},
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    logger.info(f"Brief {brief_id} actualizado a status={status}")
    return result.get("data", result)
