"""Carga los recursos editoriales (voice + formatos) al arrancar el Writer.

Lee archivos markdown de editorial/ y los devuelve como strings
para inyectar en los prompts del LLM.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_EDITORIAL_DIR = Path(__file__).resolve().parent.parent.parent / "editorial"


def load_voice(editorial_dir: str | Path = DEFAULT_EDITORIAL_DIR) -> str:
    """Lee editorial/voice.md y retorna su contenido como string.

    Raises:
        FileNotFoundError: Si voice.md no existe.
    """
    voice_path = Path(editorial_dir) / "voice.md"
    if not voice_path.exists():
        raise FileNotFoundError(
            f"voice.md no encontrado en {voice_path}. "
            "El Writer no puede arrancar sin el manual de estilo."
        )
    content = voice_path.read_text(encoding="utf-8")
    logger.info(f"Voice guide cargada: {len(content)} chars")
    return content


def load_formats(editorial_dir: str | Path = DEFAULT_EDITORIAL_DIR) -> dict[str, str]:
    """Lee todos los .md de editorial/formats/ y retorna un dict {nombre: contenido}.

    Raises:
        FileNotFoundError: Si el directorio no existe o está vacío.
    """
    formats_dir = Path(editorial_dir) / "formats"
    if not formats_dir.exists():
        raise FileNotFoundError(
            f"Directorio de formatos no encontrado: {formats_dir}. "
            "El Writer necesita al menos un formato para arrancar."
        )

    formats = {}
    for md_file in sorted(formats_dir.glob("*.md")):
        name = md_file.stem  # "analysis.md" → "analysis"
        formats[name] = md_file.read_text(encoding="utf-8")
        logger.info(f"Formato cargado: {name} ({len(formats[name])} chars)")

    if not formats:
        raise FileNotFoundError(
            f"No se encontraron archivos .md en {formats_dir}. "
            "El Writer necesita al menos un formato para arrancar."
        )

    logger.info(f"Total formatos cargados: {len(formats)}")
    return formats
