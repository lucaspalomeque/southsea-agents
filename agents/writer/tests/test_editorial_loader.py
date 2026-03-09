"""Tests para editorial_loader.py."""

import tempfile
import unittest
from pathlib import Path

from agents.writer.editorial_loader import load_voice, load_formats


class TestLoadVoice(unittest.TestCase):
    def test_loads_voice_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            voice_path = Path(tmpdir) / "voice.md"
            voice_path.write_text("# Voice\nTono analítico.", encoding="utf-8")

            result = load_voice(tmpdir)

            self.assertIn("Voice", result)
            self.assertIn("Tono analítico", result)

    def test_error_if_voice_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(FileNotFoundError) as ctx:
                load_voice(tmpdir)
            self.assertIn("voice.md", str(ctx.exception))


class TestLoadFormats(unittest.TestCase):
    def test_loads_all_formats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            formats_dir = Path(tmpdir) / "formats"
            formats_dir.mkdir()
            (formats_dir / "analysis.md").write_text("# Analysis", encoding="utf-8")
            (formats_dir / "breaking.md").write_text("# Breaking", encoding="utf-8")

            result = load_formats(tmpdir)

            self.assertEqual(set(result.keys()), {"analysis", "breaking"})
            self.assertIn("Analysis", result["analysis"])
            self.assertIn("Breaking", result["breaking"])

    def test_error_if_formats_dir_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(FileNotFoundError):
                load_formats(tmpdir)

    def test_error_if_formats_dir_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            formats_dir = Path(tmpdir) / "formats"
            formats_dir.mkdir()

            with self.assertRaises(FileNotFoundError) as ctx:
                load_formats(tmpdir)
            self.assertIn("No se encontraron", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
