"""Carga editorial para el Editor Agent.

Reutiliza la misma lógica del Writer — ambos necesitan voice.md y formatos
para evaluar alineación con la marca.
"""

from agents.writer.editorial_loader import load_voice, load_formats

__all__ = ["load_voice", "load_formats"]
