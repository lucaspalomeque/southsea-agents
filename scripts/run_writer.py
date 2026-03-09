"""Runner script para ejecutar el Writer Agent en modo preview.

Genera el artículo pero NO lo guarda en Supabase.
Muestra el artículo completo para revisión de calidad.
"""

import logging
import os
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

from agents.writer.editorial_loader import load_voice, load_formats
from agents.writer.format_selector import select_format
from agents.writer.content_generator import generate_article
from agents.writer.supabase_io import fetch_pending_briefs

if __name__ == "__main__":
    # Cargar editorial
    voice = load_voice("editorial")
    formats = load_formats("editorial")

    # Leer briefs pendientes
    briefs = fetch_pending_briefs(limit=1)
    if not briefs:
        print("No hay briefs pendientes con status=pending_writing")
        exit(0)

    brief = briefs[0]
    print(f"\n{'='*70}")
    print("BRIEF DE ENTRADA")
    print(f"{'='*70}")
    print(f"ID:              {brief.get('id', '?')}")
    print(f"Título:          {brief.get('title', '?')}")
    print(f"Ángulo:          {brief.get('editorial_angle', '?')}")
    print(f"Tags:            {brief.get('tags', brief.get('topics', []))}")
    print(f"Entidades:       {brief.get('key_entities', [])}")
    print(f"Hechos verif.:   {brief.get('verified_facts', [])}")
    print(f"Notas research:  {brief.get('research_notes', '?')[:200]}...")

    # Seleccionar formato
    format_name = select_format(brief, list(formats.keys()))
    format_template = formats[format_name]

    # Generar artículo
    article = generate_article(brief, voice, format_template, format_name)

    print(f"\n{'='*70}")
    print("ARTÍCULO GENERADO")
    print(f"{'='*70}")
    print(f"Formato:  {format_name}")
    print(f"Título:   {article['title']}")
    print(f"\n--- EXCERPT ({len(article['excerpt'])} chars) ---")
    print(article["excerpt"])
    print(f"\n--- CONTENIDO COMPLETO ({len(article['content'])} chars) ---\n")
    print(article["content"])
    print(f"\n{'='*70}")
