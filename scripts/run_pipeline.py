"""Pipeline Orchestrator — ejecuta Scout → Analyst → Writer → Editor en secuencia.

Cada agente se wrappea con métricas (tiempo, éxitos, errores).
Un agente que falla no tumba el pipeline.
Logging dual: archivo en logs/ + consola.
"""

import dataclasses
import logging
import signal
import sys
import time
import traceback
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Project root en sys.path (necesario para imports de agents/ y core/)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ---------------------------------------------------------------------------
# .env
# ---------------------------------------------------------------------------
env_path = Path(__file__).resolve().parent.parent / ".env"
if not env_path.exists():
    env_path = Path.home() / "Projects" / "southsea-agents" / ".env"
load_dotenv(env_path)

# ---------------------------------------------------------------------------
# Timeouts por agente (segundos) — ajustar con datos reales
# ---------------------------------------------------------------------------
AGENT_TIMEOUTS = {
    "scout": 300,    # 5 min — no usa LLM pesado
    "analyst": 900,  # 15 min — Sonnet + hasta 10 items
    "writer": 900,   # 15 min — Sonnet + hasta 10 items
    "editor": 600,   # 10 min — Haiku pero múltiples dimensiones
}

RETRY_BACKOFF_SECONDS = 30
MAX_LOG_FILES = 30

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

logger = logging.getLogger("orchestrator")


# ---------------------------------------------------------------------------
# AgentResult
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class AgentResult:
    agent_name: str
    items_success: int = 0
    items_error: int = 0
    errors: list = dataclasses.field(default_factory=list)
    duration_seconds: float = 0.0
    status: str = "ok"  # ok | failed | timeout | retry_ok | retry_failed


# ---------------------------------------------------------------------------
# Timeout context manager (signal.alarm — main thread, Mac/Linux)
# ---------------------------------------------------------------------------
@contextmanager
def timeout(seconds: int):
    """Raises TimeoutError if the block takes longer than `seconds`."""
    def _handler(signum, frame):
        raise TimeoutError(f"Timeout after {seconds}s")

    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


# ---------------------------------------------------------------------------
# Agent factories (lazy imports)
# ---------------------------------------------------------------------------
def make_scout():
    from agents.scout.scout_agent import ScoutAgent
    return ScoutAgent()


def make_analyst():
    from agents.analyst.analyst_agent import AnalystAgent
    return AnalystAgent(batch_size=10)


def make_writer():
    from agents.writer.writer_agent import WriterAgent
    return WriterAgent(batch_size=10, editorial_dir="editorial")


def make_editor():
    from agents.editor.editor_agent import EditorAgent
    return EditorAgent(batch_size=10, editorial_dir="editorial")


PIPELINE = [
    ("scout", make_scout),
    ("analyst", make_analyst),
    ("writer", make_writer),
    ("editor", make_editor),
]


# ---------------------------------------------------------------------------
# Wrapper: ejecuta un agente con métricas, timeout y retry
# ---------------------------------------------------------------------------
def run_agent_with_metrics(
    agent_name: str,
    factory,
    timeout_seconds: int = 300,
    retry_backoff: int = RETRY_BACKOFF_SECONDS,
) -> AgentResult:
    """Instancia y ejecuta un agente, midiendo tiempo y capturando errores."""

    def _attempt():
        agent = factory()
        with timeout(timeout_seconds):
            return agent.run()

    start = time.time()
    first_error_msg = ""

    # Primer intento
    try:
        result = _attempt()
        elapsed = time.time() - start
        logger.info(f"{agent_name}: {len(result)} items procesados en {elapsed:.1f}s")
        return AgentResult(
            agent_name=agent_name,
            items_success=len(result),
            duration_seconds=elapsed,
            status="ok",
        )
    except Exception as first_error:
        first_error_msg = str(first_error)
        first_tb = traceback.format_exc()
        status_label = "timeout" if isinstance(first_error, TimeoutError) else "error"
        logger.warning(
            f"{agent_name}: {status_label} en primer intento — {first_error}. "
            f"Retry en {retry_backoff}s..."
        )

    # Retry
    time.sleep(retry_backoff)
    try:
        result = _attempt()
        elapsed = time.time() - start
        logger.info(
            f"{agent_name}: retry exitoso — {len(result)} items en {elapsed:.1f}s"
        )
        return AgentResult(
            agent_name=agent_name,
            items_success=len(result),
            duration_seconds=elapsed,
            status="retry_ok",
        )
    except Exception as retry_error:
        elapsed = time.time() - start
        logger.error(f"{agent_name}: falló tras retry — {retry_error}")
        logger.debug(first_tb)
        return AgentResult(
            agent_name=agent_name,
            items_error=1,
            errors=[first_error_msg, str(retry_error)],
            duration_seconds=elapsed,
            status="retry_failed",
        )


# ---------------------------------------------------------------------------
# Logging setup (dual: archivo + consola)
# ---------------------------------------------------------------------------
def setup_logging(log_dir: Path = LOG_DIR) -> Path:
    """Configura logging dual y devuelve el path del archivo de log."""
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = log_dir / f"pipeline_{timestamp}.log"

    fmt = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Limpiar handlers previos (por si se llama más de una vez)
    root.handlers.clear()

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    root.addHandler(console_handler)

    return log_path


# ---------------------------------------------------------------------------
# Log rotation
# ---------------------------------------------------------------------------
def rotate_logs(log_dir: Path = LOG_DIR, max_files: int = MAX_LOG_FILES):
    """Borra los logs más viejos si hay más de max_files."""
    log_files = sorted(log_dir.glob("pipeline_*.log"), key=lambda p: p.stat().st_mtime)
    while len(log_files) > max_files:
        oldest = log_files.pop(0)
        oldest.unlink()
        logger.info(f"Log rotado: {oldest.name}")


# ---------------------------------------------------------------------------
# Reporte final
# ---------------------------------------------------------------------------
AGENT_LABELS = {
    "scout": "Scout",
    "analyst": "Analyst",
    "writer": "Writer",
    "editor": "Editor",
}


def generate_report(results: list[AgentResult], start_time: datetime, end_time: datetime) -> str:
    """Genera el reporte final del pipeline."""
    duration = end_time - start_time
    total_seconds = duration.total_seconds()
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)

    lines = [
        "",
        "═" * 50,
        f"  PIPELINE REPORT — {start_time:%Y-%m-%d %H:%M UTC}",
        "═" * 50,
        "",
    ]

    for r in results:
        label = AGENT_LABELS.get(r.agent_name, r.agent_name)
        if r.status in ("ok", "retry_ok"):
            detail = f"{r.items_success} processed"
            if r.status == "retry_ok":
                detail += " (after retry)"
        else:
            detail = f"FAILED — {', '.join(r.errors[:2])}"
        lines.append(f"  {label:10s} {detail}")

    total_success = sum(r.items_success for r in results)
    failed_agents = [r for r in results if r.status == "retry_failed"]

    if failed_agents:
        overall = f"⚠ PARTIAL ({len(failed_agents)} agent(s) failed)"
    elif total_success == 0:
        overall = "✅ OK (pipeline empty, nothing to process)"
    else:
        overall = f"✅ OK ({total_success} items through pipeline)"

    lines.extend([
        "",
        f"  Duration: {minutes}m {seconds:02d}s",
        f"  Status:   {overall}",
        "",
        "═" * 50,
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------
def run_pipeline() -> list[AgentResult]:
    """Ejecuta el pipeline completo: Scout → Analyst → Writer → Editor."""
    log_path = setup_logging()
    rotate_logs()

    start_time = datetime.now()
    logger.info("Pipeline iniciado")
    logger.info(f"Log: {log_path}")

    results = []
    for agent_name, factory in PIPELINE:
        logger.info(f"{'─' * 40}")
        logger.info(f"Ejecutando {AGENT_LABELS.get(agent_name, agent_name)}...")
        timeout_s = AGENT_TIMEOUTS.get(agent_name, 300)
        result = run_agent_with_metrics(agent_name, factory, timeout_seconds=timeout_s)
        results.append(result)

    end_time = datetime.now()
    report = generate_report(results, start_time, end_time)
    logger.info(report)

    from core.telegram_notifier import send_report
    send_report(report)

    logger.info("Pipeline finalizado")

    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_pipeline()
