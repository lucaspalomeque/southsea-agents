"""Parser de AGENT.md — carga secciones, prompts y configuración por agente.

Cada agente tiene un AGENT.md en agents/<nombre>/AGENT.md con secciones
markdown que definen su identidad, prompts, reglas, etc.

Uso:
    from core.agent_config import get_prompt, get_section

    prompt = get_prompt("scout", "classifier")
    rules = get_section("scout", "Rules")
"""

import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"


def load_agent_md(agent_name: str) -> dict[str, str]:
    """Lee y parsea el AGENT.md de un agente en secciones.

    Args:
        agent_name: Nombre del agente (scout, analyst, writer, editor).

    Returns:
        Dict donde las keys son nombres de sección (sin ##) y los values
        son el contenido de cada sección.

    Raises:
        FileNotFoundError: Si el AGENT.md no existe.
    """
    path = AGENTS_DIR / agent_name / "AGENT.md"
    if not path.exists():
        raise FileNotFoundError(f"AGENT.md no encontrado: {path}")

    content = path.read_text(encoding="utf-8")
    sections = _parse_sections(content)

    logger.info(f"AGENT.md cargado: {agent_name} — {len(sections)} secciones")
    return sections


def _parse_sections(content: str) -> dict[str, str]:
    """Parsea contenido markdown en secciones por headers ##.

    Ignora el header # (título del documento).
    Soporta headers ## y ## con sufijos (e.g., ## Prompt: classifier).
    """
    sections: dict[str, str] = {}
    current_header = None
    current_lines: list[str] = []

    for line in content.split("\n"):
        # Match ## headers (but not # or ###)
        match = re.match(r"^## (.+)$", line)
        if match:
            # Save previous section
            if current_header is not None:
                sections[current_header] = "\n".join(current_lines).strip()
            current_header = match.group(1).strip()
            current_lines = []
        elif current_header is not None:
            current_lines.append(line)

    # Save last section
    if current_header is not None:
        sections[current_header] = "\n".join(current_lines).strip()

    return sections


def get_section(agent_name: str, section: str) -> str:
    """Obtiene una sección específica del AGENT.md de un agente.

    Args:
        agent_name: Nombre del agente.
        section: Nombre exacto de la sección (sin ##).

    Returns:
        Contenido de la sección.

    Raises:
        FileNotFoundError: Si el AGENT.md no existe.
        KeyError: Si la sección no existe.
    """
    sections = load_agent_md(agent_name)
    if section not in sections:
        available = list(sections.keys())
        raise KeyError(
            f"Sección '{section}' no encontrada en {agent_name}/AGENT.md. "
            f"Secciones disponibles: {available}"
        )
    return sections[section]


def get_prompt(agent_name: str, task_name: str) -> str:
    """Obtiene un prompt específico del AGENT.md de un agente.

    Busca la sección '## Prompt: <task_name>'.

    Args:
        agent_name: Nombre del agente.
        task_name: Nombre del task (classifier, researcher, etc.).

    Returns:
        Texto del prompt.

    Raises:
        FileNotFoundError: Si el AGENT.md no existe.
        KeyError: Si el prompt no existe.
    """
    section_name = f"Prompt: {task_name}"
    return get_section(agent_name, section_name)
