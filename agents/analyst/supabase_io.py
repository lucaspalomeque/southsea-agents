"""Comunicación con Supabase via Edge Functions para el Analyst Agent.

Endpoints:
- agent-read:   POST {table, filters, limit} → {success, data, count}
- agent-ingest:  POST {table, record}         → {success, data}
- agent-update:  POST {table, id, updates}    → {success, data}

Todos autenticados con x-agent-key.
"""

import logging

import httpx

from core.config import SUPABASE_URL, AGENTS_API_KEY

logger = logging.getLogger(__name__)

BASE_URL = SUPABASE_URL.replace("/functions/v1/agent-ingest", "")
READ_URL = f"{BASE_URL}/functions/v1/agent-read"
INGEST_URL = f"{BASE_URL}/functions/v1/agent-ingest"
UPDATE_URL = f"{BASE_URL}/functions/v1/agent-update"

HEADERS = {
    "x-agent-key": AGENTS_API_KEY,
    "Content-Type": "application/json",
}
TIMEOUT = 30


def fetch_pending_items(limit: int = 10) -> list[dict]:
    """Lee scout_items con status=pending_analysis."""
    response = httpx.post(
        READ_URL,
        headers=HEADERS,
        json={
            "table": "scout_items",
            "filters": {"status": "pending_analysis"},
            "limit": limit,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    items = result.get("data", [])
    logger.info(f"Fetched {len(items)} pending items")
    return items


def update_scout_item(item_id: str, updates: dict) -> dict:
    """Actualiza campos de un scout_item existente."""
    response = httpx.post(
        UPDATE_URL,
        headers=HEADERS,
        json={
            "table": "scout_items",
            "id": item_id,
            "updates": updates,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    logger.info(f"Updated scout_item {item_id}: {updates}")
    return result.get("data", result)


def save_brief(brief: dict) -> dict:
    """Guarda un analyst_brief en Supabase.

    agent-ingest espera campos flat con 'table' como campo adicional.
    """
    body = {**brief, "table": "analyst_briefs"}
    response = httpx.post(
        INGEST_URL,
        headers=HEADERS,
        json=body,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    logger.info(f"Saved brief for scout_item {brief.get('scout_item_id')}")
    return result.get("data", result)
