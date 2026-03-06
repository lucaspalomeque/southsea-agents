"""Runner script para ejecutar el Analyst Agent con .env cargado."""

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

from agents.analyst.analyst_agent import AnalystAgent

if __name__ == "__main__":
    agent = AnalystAgent(batch_size=10)
    results = agent.run()
    print(f"\n{'='*60}")
    print(f"Briefs generados: {len(results)}")
    for r in results:
        print(f"  - {r.get('title', r.get('scout_item_id', '?'))}")
    print(f"{'='*60}")
