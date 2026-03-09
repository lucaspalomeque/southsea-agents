"""Tests para editorial_loader.py del Editor.

Verifica que reutiliza correctamente la lógica del Writer.
"""

import unittest
from unittest.mock import patch

from agents.editor.editorial_loader import load_voice, load_formats


class TestEditorialLoaderReuse(unittest.TestCase):
    """Verifica que el Editor usa las mismas funciones que el Writer."""

    @patch("agents.writer.editorial_loader.Path")
    def test_load_voice_delegates_to_writer(self, mock_path):
        """load_voice del editor es la misma función que la del writer."""
        from agents.writer.editorial_loader import load_voice as writer_load_voice
        self.assertIs(load_voice, writer_load_voice)

    @patch("agents.writer.editorial_loader.Path")
    def test_load_formats_delegates_to_writer(self, mock_path):
        """load_formats del editor es la misma función que la del writer."""
        from agents.writer.editorial_loader import load_formats as writer_load_formats
        self.assertIs(load_formats, writer_load_formats)


if __name__ == "__main__":
    unittest.main()
