"""Test script para verificar si el endpoint agent-update existe y funciona.

Prueba ambos esquemas de auth (Bearer y x-agent-key) para descubrir cual usa cada endpoint.
"""

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
UPDATE_URL = f"{BASE_URL}/functions/v1/agent-update"
TIMEOUT = 30

AUTH_SCHEMES = {
    "Bearer": {
        "Authorization": f"Bearer {AGENTS_API_KEY}",
        "Content-Type": "application/json",
    },
    "x-agent-key": {
        "x-agent-key": AGENTS_API_KEY,
        "Content-Type": "application/json",
    },
}


def step(n, desc):
    print(f"\n{'='*60}")
    print(f"PASO {n}: {desc}")
    print(f"{'='*60}")


def try_post(url, body, label=""):
    """Prueba un POST con ambos esquemas de auth. Retorna (response, scheme) del que funcione."""
    for scheme_name, headers in AUTH_SCHEMES.items():
        print(f"  Probando {scheme_name}... ", end="")
        resp = httpx.post(url, headers=headers, json=body, timeout=TIMEOUT)
        print(f"status={resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"  Response: {data}")
            return data, scheme_name
        else:
            try:
                print(f"  Response: {resp.json()}")
            except Exception:
                print(f"  Response: {resp.text[:200]}")

    return None, None


def post(url, headers, body):
    resp = httpx.post(url, headers=headers, json=body, timeout=TIMEOUT)
    print(f"  Status: {resp.status_code}")
    data = resp.json()
    print(f"  Response: {data}")
    resp.raise_for_status()
    return data


def main():
    print(f"BASE_URL: {BASE_URL}")
    print(f"READ_URL: {READ_URL}")
    print(f"UPDATE_URL: {UPDATE_URL}")
    print(f"API_KEY: {AGENTS_API_KEY[:12]}...")

    # --- PASO 1: Descubrir auth de agent-read ---
    step(1, "Leer scout_item con status=pending_analysis (descubrir auth)")
    body = {"table": "scout_items", "filters": {"status": "pending_analysis"}, "limit": 1}
    result, read_scheme = try_post(READ_URL, body)

    if result is None:
        print("\n  FALLO: agent-read no responde con ningun esquema de auth.")
        print("  Verificar que el endpoint existe y la API key es correcta.")
        sys.exit(1)

    print(f"\n  agent-read usa: {read_scheme}")
    read_headers = AUTH_SCHEMES[read_scheme]

    items = result.get("data", result if isinstance(result, list) else [])
    if not items:
        print("\n  No hay items con status pending_analysis. No se puede testear.")
        sys.exit(1)

    item = items[0]
    item_id = item["id"]
    print(f"\n  Item encontrado: id={item_id}, title={item.get('title', '?')}")

    # --- PASO 2: Probar agent-update ---
    step(2, f"UPDATE status -> in_analysis (id={item_id})")
    body = {"table": "scout_items", "id": item_id, "updates": {"status": "in_analysis"}}
    result, update_scheme = try_post(UPDATE_URL, body)

    if result is None:
        print("\n  FALLO: agent-update no responde con ningun esquema de auth.")
        print("  El endpoint probablemente NO EXISTE. Hay que crearlo en Lovable.")
        sys.exit(1)

    print(f"\n  agent-update usa: {update_scheme}")
    update_headers = AUTH_SCHEMES[update_scheme]

    # --- PASO 3: Verificar update ---
    step(3, "Verificar: leer item con status=in_analysis")
    body = {"table": "scout_items", "filters": {"status": "in_analysis", "id": item_id}, "limit": 1}
    result = post(READ_URL, read_headers, body)

    items = result.get("data", result if isinstance(result, list) else [])
    if items and items[0]["id"] == item_id:
        print(f"\n  CONFIRMADO: item {item_id} tiene status=in_analysis")
    else:
        print(f"\n  ERROR: no se encontro el item con status=in_analysis")
        step("3b", "Intentando restaurar...")
        post(UPDATE_URL, update_headers,
             {"table": "scout_items", "id": item_id, "updates": {"status": "pending_analysis"}})
        sys.exit(1)

    # --- PASO 4: Restaurar ---
    step(4, f"Restaurar status -> pending_analysis (id={item_id})")
    post(UPDATE_URL, update_headers,
         {"table": "scout_items", "id": item_id, "updates": {"status": "pending_analysis"}})

    # --- PASO 5: Verificar restauracion ---
    step(5, "Verificar restauracion")
    body = {"table": "scout_items", "filters": {"status": "pending_analysis", "id": item_id}, "limit": 1}
    result = post(READ_URL, read_headers, body)

    items = result.get("data", result if isinstance(result, list) else [])
    if items and items[0]["id"] == item_id:
        print(f"\n  RESTAURADO: item {item_id} vuelve a pending_analysis")
    else:
        print(f"\n  ADVERTENCIA: no se pudo confirmar la restauracion")

    print(f"\n{'='*60}")
    print(f"RESULTADO: agent-read ({read_scheme}) y agent-update ({update_scheme}) FUNCIONAN")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
