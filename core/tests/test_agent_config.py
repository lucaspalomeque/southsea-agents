"""Tests para core/agent_config.py — parser de AGENT.md."""

import pytest
from pathlib import Path
from unittest.mock import patch

from core.agent_config import load_agent_md, get_prompt, get_section, _parse_sections


SAMPLE_AGENT_MD = """# Scout Agent — The Southmetaverse Sea

## Identity
You are the Scout, the eyes and ears of the newsroom.

## Mission
Monitor sources and collect relevant information.

## Prompt: classifier
Classify each news item into topics.

Valid topics: crypto_defi, web3

Items to classify:

## Prompt: secondary_task
This is a secondary prompt.

## Rules
- Only assign relevant topics
- Deduplicate by URL

## Tools
- rss_fetcher
- deduplicator
"""


class TestParseSections:
    def test_parses_all_sections(self):
        sections = _parse_sections(SAMPLE_AGENT_MD)
        assert "Identity" in sections
        assert "Mission" in sections
        assert "Prompt: classifier" in sections
        assert "Prompt: secondary_task" in sections
        assert "Rules" in sections
        assert "Tools" in sections

    def test_ignores_h1_header(self):
        sections = _parse_sections(SAMPLE_AGENT_MD)
        # H1 title should not be a section
        assert "Scout Agent — The Southmetaverse Sea" not in sections

    def test_section_content_is_stripped(self):
        sections = _parse_sections(SAMPLE_AGENT_MD)
        assert sections["Identity"] == "You are the Scout, the eyes and ears of the newsroom."

    def test_multiline_section(self):
        sections = _parse_sections(SAMPLE_AGENT_MD)
        assert "- Only assign relevant topics" in sections["Rules"]
        assert "- Deduplicate by URL" in sections["Rules"]

    def test_prompt_section_preserves_content(self):
        sections = _parse_sections(SAMPLE_AGENT_MD)
        prompt = sections["Prompt: classifier"]
        assert "Classify each news item" in prompt
        assert "Items to classify:" in prompt


class TestLoadAgentMd:
    def test_loads_real_agent(self, tmp_path):
        agent_dir = tmp_path / "test_agent"
        agent_dir.mkdir()
        (agent_dir / "AGENT.md").write_text(SAMPLE_AGENT_MD)

        with patch("core.agent_config.AGENTS_DIR", tmp_path):
            sections = load_agent_md("test_agent")

        assert len(sections) == 6
        assert "Identity" in sections

    def test_file_not_found(self, tmp_path):
        with patch("core.agent_config.AGENTS_DIR", tmp_path):
            with pytest.raises(FileNotFoundError, match="AGENT.md no encontrado"):
                load_agent_md("nonexistent")


class TestGetSection:
    def test_gets_existing_section(self, tmp_path):
        agent_dir = tmp_path / "test_agent"
        agent_dir.mkdir()
        (agent_dir / "AGENT.md").write_text(SAMPLE_AGENT_MD)

        with patch("core.agent_config.AGENTS_DIR", tmp_path):
            result = get_section("test_agent", "Mission")

        assert result == "Monitor sources and collect relevant information."

    def test_missing_section_raises_key_error(self, tmp_path):
        agent_dir = tmp_path / "test_agent"
        agent_dir.mkdir()
        (agent_dir / "AGENT.md").write_text(SAMPLE_AGENT_MD)

        with patch("core.agent_config.AGENTS_DIR", tmp_path):
            with pytest.raises(KeyError, match="Sección 'Nonexistent' no encontrada"):
                get_section("test_agent", "Nonexistent")


class TestGetPrompt:
    def test_gets_prompt_by_task_name(self, tmp_path):
        agent_dir = tmp_path / "test_agent"
        agent_dir.mkdir()
        (agent_dir / "AGENT.md").write_text(SAMPLE_AGENT_MD)

        with patch("core.agent_config.AGENTS_DIR", tmp_path):
            prompt = get_prompt("test_agent", "classifier")

        assert "Classify each news item" in prompt

    def test_gets_secondary_prompt(self, tmp_path):
        agent_dir = tmp_path / "test_agent"
        agent_dir.mkdir()
        (agent_dir / "AGENT.md").write_text(SAMPLE_AGENT_MD)

        with patch("core.agent_config.AGENTS_DIR", tmp_path):
            prompt = get_prompt("test_agent", "secondary_task")

        assert "secondary prompt" in prompt

    def test_missing_prompt_raises_key_error(self, tmp_path):
        agent_dir = tmp_path / "test_agent"
        agent_dir.mkdir()
        (agent_dir / "AGENT.md").write_text(SAMPLE_AGENT_MD)

        with patch("core.agent_config.AGENTS_DIR", tmp_path):
            with pytest.raises(KeyError, match="Prompt: nonexistent"):
                get_prompt("test_agent", "nonexistent")
