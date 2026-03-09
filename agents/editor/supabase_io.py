"""Comunicación con Supabase via Edge Functions para el Editor Agent.

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


def fetch_pending_posts(limit: int = 10) -> list[dict]:
    """Lee posts con status=pending_editing."""
    response = httpx.post(
        READ_URL,
        headers=HEADERS,
        json={
            "table": "posts",
            "filters": {"status": "pending_review"},
            "limit": limit,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    items = result.get("data", [])
    logger.info(f"Fetched {len(items)} pending posts for editing")
    return items


def fetch_brief(brief_id: str) -> dict | None:
    """Lee un analyst_brief por ID."""
    response = httpx.post(
        READ_URL,
        headers=HEADERS,
        json={
            "table": "analyst_briefs",
            "filters": {"id": brief_id},
            "limit": 1,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    items = result.get("data", [])
    if not items:
        logger.warning(f"Brief {brief_id} no encontrado")
        return None
    return items[0]


def save_review(review: dict) -> dict:
    """Guarda una review en editor_reviews via agent-ingest.

    Esquema de editor_reviews:
        post_id, voice_alignment, factual_rigor, format_compliance,
        thematic_alignment, overall_score, decision, summary, revision_notes
    """
    body = {
        "table": "editor_reviews",
        "post_id": review["post_id"],
        "decision": review["decision"],
        "voice_alignment": review.get("voice_alignment"),
        "factual_rigor": review.get("factual_rigor"),
        "format_compliance": review.get("format_compliance"),
        "thematic_alignment": review.get("thematic_alignment"),
        "overall_score": review.get("overall_score"),
        "summary": review.get("summary"),
        "revision_notes": review.get("revision_notes"),
    }
    # Remove None values to let DB defaults apply
    body = {k: v for k, v in body.items() if v is not None}
    response = httpx.post(
        INGEST_URL,
        headers=HEADERS,
        json=body,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    logger.info(f"Review guardada para post {review.get('post_id', '?')}")
    return result.get("data", result)


def approve_post(post_id: str) -> dict:
    """Marca post como aprobado por editor. Status se mantiene pending_review para el humano."""
    response = httpx.post(
        UPDATE_URL,
        headers=HEADERS,
        json={
            "table": "posts",
            "id": post_id,
            "updates": {"editor_approved": True},
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    logger.info(f"Post {post_id} aprobado por editor")
    return result.get("data", result)


def return_post(post_id: str, revision_count: int) -> dict:
    """Devuelve post al Writer cambiando status a draft e incrementando revision_count."""
    response = httpx.post(
        UPDATE_URL,
        headers=HEADERS,
        json={
            "table": "posts",
            "id": post_id,
            "updates": {
                "status": "draft",
                "revision_count": revision_count + 1,
            },
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    logger.info(f"Post {post_id} devuelto → draft (revision_count={revision_count + 1})")
    return result.get("data", result)
