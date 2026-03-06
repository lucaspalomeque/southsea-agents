"""Test script para verificar que agent-read funciona correctamente."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
if not env_path.exists():
    env_path = Path.home() / "Projects" / "southsea-agents" / ".env"
load_dotenv(env_path)

import httpx

SUPABASE_URL = os.environ["SUPABASE_URL"]
AGENTS_API_KEY = os.environ["AGENTS_API_KEY"]

BASE_URL = SUPABASE_URL.replace("/functions/v1/agent-ingest", "")
READ_URL = f"{BASE_URL}/functions/v1/agent-read"
HEADERS = {
    "x-agent-key": AGENTS_API_KEY,
    "Content-Type": "application/json",
}
TIMEOUT = 30


def step(n, desc):
    print(f"\n{'='*60}")
    print(f"PASO {n}: {desc}")
    print(f"{'='*60}")


def read(table, filters=None, limit=5):
    body = {"table": table, "filters": filters or {}, "limit": limit}
    print(f"  POST {READ_URL}")
    print(f"  Body: {body}")
    resp = httpx.post(READ_URL, headers=HEADERS, json=body, timeout=TIMEOUT)
    print(f"  Status: {resp.status_code}")
    data = resp.json()
    print(f"  Response: {data}")
    return resp.status_code, data


def main():
    ok = 0
    fail = 0

    # 1. Leer scout_items sin filtro
    step(1, "Leer scout_items (sin filtro, limit 3)")
    status, data = read("scout_items", limit=3)
    if status == 200 and "data" in data:
        print(f"\n  OK — {data.get('count', len(data['data']))} items")
        ok += 1
    else:
        print(f"\n  FALLO")
        fail += 1

    # 2. Leer scout_items con filtro de status
    step(2, "Leer scout_items con status=pending_analysis")
    status, data = read("scout_items", {"status": "pending_analysis"}, limit=3)
    if status == 200 and "data" in data:
        print(f"\n  OK — {data.get('count', len(data['data']))} items pending_analysis")
        ok += 1
    else:
        print(f"\n  FALLO")
        fail += 1

    # 3. Leer analyst_briefs
    step(3, "Leer analyst_briefs (sin filtro)")
    status, data = read("analyst_briefs", limit=3)
    if status == 200 and "data" in data:
        print(f"\n  OK — {data.get('count', len(data['data']))} briefs")
        ok += 1
    else:
        print(f"\n  FALLO")
        fail += 1

    # 4. Leer tabla no existente
    step(4, "Leer tabla inexistente (debe fallar)")
    status, data = read("tabla_falsa")
    if status != 200:
        print(f"\n  OK — rechazado correctamente ({status})")
        ok += 1
    else:
        print(f"\n  ADVERTENCIA — no rechazó tabla inexistente")
        fail += 1

    print(f"\n{'='*60}")
    print(f"RESULTADO: {ok} OK, {fail} FALLO")
    print(f"{'='*60}")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
