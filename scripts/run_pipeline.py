"""Runner script — pipeline completo: Scout → Analyst → Writer → Editor.

Ejecuta los 4 agentes en secuencia y muestra los resultados del Editor.
"""

import json
import logging
import sys
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
logger = logging.getLogger("pipeline")


def run_scout():
    from agents.scout.scout_agent import ScoutAgent
    logger.info("=" * 60)
    logger.info("SCOUT AGENT")
    logger.info("=" * 60)
    agent = ScoutAgent()
    results = agent.run()
    logger.info(f"Scout: {len(results)} items ingested")
    return results


def run_analyst():
    from agents.analyst.analyst_agent import AnalystAgent
    logger.info("=" * 60)
    logger.info("ANALYST AGENT")
    logger.info("=" * 60)
    agent = AnalystAgent(batch_size=5)
    results = agent.run()
    logger.info(f"Analyst: {len(results)} briefs generados")
    return results


def run_writer():
    from agents.writer.writer_agent import WriterAgent
    logger.info("=" * 60)
    logger.info("WRITER AGENT")
    logger.info("=" * 60)
    agent = WriterAgent(batch_size=5, editorial_dir="editorial")
    results = agent.run()
    logger.info(f"Writer: {len(results)} posts creados")
    return results


def run_editor():
    from agents.editor.editor_agent import EditorAgent
    logger.info("=" * 60)
    logger.info("EDITOR AGENT")
    logger.info("=" * 60)
    agent = EditorAgent(batch_size=10, editorial_dir="editorial")
    results = agent.run()
    return results


if __name__ == "__main__":
    # 1. Scout
    scout_results = run_scout()

    # 2. Analyst
    analyst_results = run_analyst()

    # 3. Writer
    writer_results = run_writer()

    # 4. Editor
    editor_results = run_editor()

    # Resumen del Editor
    print(f"\n{'=' * 70}")
    print("RESULTADOS DEL EDITOR")
    print(f"{'=' * 70}")

    if not editor_results:
        print("No se procesaron posts.")
    else:
        for i, review in enumerate(editor_results, 1):
            post_id = review.get("post_id", "?")
            decision = review.get("decision", "?")
            avg = review.get("average_score", "N/A")
            feedback = review.get("feedback", "")
            human_note = review.get("human_note")

            scores_raw = review.get("scores", "{}")
            if isinstance(scores_raw, str):
                scores = json.loads(scores_raw)
            else:
                scores = scores_raw

            print(f"\n--- Post {i} (ID: {post_id}) ---")
            print(f"  Decision:            {decision}")
            print(f"  voice_alignment:     {scores.get('voice_alignment', 'N/A')}")
            print(f"  factual_rigor:       {scores.get('factual_rigor', 'N/A')}")
            print(f"  format_compliance:   {scores.get('format_compliance', 'N/A')}")
            print(f"  thematic_alignment:  {scores.get('thematic_alignment', 'N/A')}")
            print(f"  overall_score:       {avg}")
            print(f"  Feedback:            {feedback[:200]}")
            if human_note:
                print(f"  Human note:          {human_note}")

    print(f"\n{'=' * 70}")
    print("RESUMEN PIPELINE")
    print(f"{'=' * 70}")
    print(f"  Scout:    {len(scout_results)} items")
    print(f"  Analyst:  {len(analyst_results)} briefs")
    print(f"  Writer:   {len(writer_results)} posts")
    print(f"  Editor:   {len(editor_results)} reviews")
    print(f"{'=' * 70}")
