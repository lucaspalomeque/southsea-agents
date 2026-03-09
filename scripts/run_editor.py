"""Runner script para ejecutar solo el Editor Agent."""

import json
import logging
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
if not env_path.exists():
    env_path = Path.home() / "Projects" / "southsea-agents" / ".env"
load_dotenv(env_path)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

import httpx
from core.config import SUPABASE_URL, AGENTS_API_KEY
from agents.editor.editor_agent import EditorAgent

HEADERS = {"x-agent-key": AGENTS_API_KEY, "Content-Type": "application/json"}


def verify_persistence():
    """Lee editor_reviews y posts de Supabase para verificar persistencia."""
    # Reviews
    r = httpx.post(
        f"{SUPABASE_URL}/functions/v1/agent-read",
        headers=HEADERS,
        json={"table": "editor_reviews", "filters": {}, "limit": 50},
        timeout=30,
    )
    reviews = r.json().get("data", [])

    # Posts with editor_approved=true
    r2 = httpx.post(
        f"{SUPABASE_URL}/functions/v1/agent-read",
        headers=HEADERS,
        json={"table": "posts", "filters": {"editor_approved": True}, "limit": 50},
        timeout=30,
    )
    approved_posts = r2.json().get("data", [])

    # Posts with status=draft (returned by editor)
    r3 = httpx.post(
        f"{SUPABASE_URL}/functions/v1/agent-read",
        headers=HEADERS,
        json={"table": "posts", "filters": {"status": "draft"}, "limit": 50},
        timeout=30,
    )
    draft_posts = r3.json().get("data", [])

    return reviews, approved_posts, draft_posts


if __name__ == "__main__":
    agent = EditorAgent(batch_size=10, editorial_dir="editorial")
    results = agent.run()

    print(f"\n{'=' * 70}")
    print(f"EDITOR RESULTS — {len(results)} posts evaluados")
    print(f"{'=' * 70}")

    for i, review in enumerate(results, 1):
        print(f"\n--- Post {i} ---")
        print(f"  Post ID:             {review.get('post_id', '?')}")
        print(f"  Decision:            {review.get('decision', '?')}")
        print(f"  voice_alignment:     {review.get('voice_alignment', 'N/A')}")
        print(f"  factual_rigor:       {review.get('factual_rigor', 'N/A')}")
        print(f"  format_compliance:   {review.get('format_compliance', 'N/A')}")
        print(f"  thematic_alignment:  {review.get('thematic_alignment', 'N/A')}")
        print(f"  overall_score:       {review.get('overall_score', 'N/A')}")
        print(f"  Summary:             {review.get('summary', '')[:200]}")
        if review.get("revision_notes"):
            print(f"  Revision notes:      {review['revision_notes']}")

    # Verificar persistencia
    print(f"\n{'=' * 70}")
    print("VERIFICACIÓN DE PERSISTENCIA EN SUPABASE")
    print(f"{'=' * 70}")

    reviews_db, approved_posts, draft_posts = verify_persistence()

    print(f"\n  editor_reviews persistidas:     {len(reviews_db)}")
    print(f"  posts con editor_approved=true: {len(approved_posts)}")
    print(f"  posts con status=draft:         {len(draft_posts)}")

    if reviews_db:
        print(f"\n  Reviews en DB:")
        for r in reviews_db:
            print(f"    - {r['id'][:8]}... | post: {r['post_id'][:8]}... | "
                  f"decision: {r.get('decision')} | "
                  f"voice: {r.get('voice_alignment')} | "
                  f"factual: {r.get('factual_rigor')} | "
                  f"format: {r.get('format_compliance')} | "
                  f"thematic: {r.get('thematic_alignment')} | "
                  f"overall: {r.get('overall_score')}")

    print(f"\n{'=' * 70}")
