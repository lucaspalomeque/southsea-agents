"""Tests para format_selector.py — selección heurística de formato."""

import unittest

from agents.writer.format_selector import select_format
from agents.writer.tests.conftest import (
    SYNTHETIC_BRIEF,
    SYNTHETIC_BRIEF_BREAKING,
    SYNTHETIC_BRIEF_EXPLAINER,
    SYNTHETIC_BRIEF_OPINION,
)

AVAILABLE = ["analysis", "breaking", "explainer", "opinion"]


class TestFormatSelector(unittest.TestCase):
    def test_breaking_few_facts_and_urgency(self):
        result = select_format(SYNTHETIC_BRIEF_BREAKING, AVAILABLE)
        self.assertEqual(result, "breaking")

    def test_explainer_researched_entities(self):
        result = select_format(SYNTHETIC_BRIEF_EXPLAINER, AVAILABLE)
        self.assertEqual(result, "explainer")

    def test_opinion_polemic_regulation(self):
        result = select_format(SYNTHETIC_BRIEF_OPINION, AVAILABLE)
        self.assertEqual(result, "opinion")

    def test_analysis_default(self):
        result = select_format(SYNTHETIC_BRIEF, AVAILABLE)
        self.assertEqual(result, "analysis")

    def test_only_returns_available_formats(self):
        # Solo analysis disponible — no puede elegir breaking
        result = select_format(SYNTHETIC_BRIEF_BREAKING, ["analysis"])
        self.assertEqual(result, "analysis")

    def test_fallback_to_first_if_no_analysis(self):
        result = select_format(SYNTHETIC_BRIEF, ["explainer", "opinion"])
        self.assertEqual(result, "explainer")


if __name__ == "__main__":
    unittest.main()
