"""Tests para evaluator.py — mock de LLM."""

import json
import unittest
from unittest.mock import patch

from agents.editor.tests.conftest import (
    SYNTHETIC_POST,
    SYNTHETIC_BRIEF,
    SYNTHETIC_VOICE,
    SYNTHETIC_FORMAT_ANALYSIS,
    SYNTHETIC_LLM_EVALUATION_APPROVED,
    SYNTHETIC_LLM_EVALUATION_VETO,
    SYNTHETIC_LLM_EVALUATION_WRAPPED,
)
from agents.editor.evaluator import evaluate, _parse_evaluation, DIMENSIONS, VETO_THRESHOLD


class TestParseEvaluation(unittest.TestCase):
    def test_parses_valid_json(self):
        result = _parse_evaluation(SYNTHETIC_LLM_EVALUATION_APPROVED)

        self.assertEqual(result["voice_alignment"], 8.0)
        self.assertEqual(result["factual_rigor"], 7.5)
        self.assertEqual(result["format_compliance"], 9.0)
        self.assertEqual(result["thematic_alignment"], 8.5)
        self.assertIn("feedback", result)
        self.assertTrue(len(result["feedback"]) > 0)

    def test_parses_json_in_code_block(self):
        result = _parse_evaluation(SYNTHETIC_LLM_EVALUATION_WRAPPED)

        self.assertEqual(result["voice_alignment"], 7.0)
        self.assertEqual(result["factual_rigor"], 6.5)
        self.assertIn("feedback", result)

    def test_raises_on_missing_dimension(self):
        bad_json = '{"voice_alignment": 8.0, "feedback": "ok"}'
        with self.assertRaises(ValueError):
            _parse_evaluation(bad_json)

    def test_raises_on_invalid_json(self):
        with self.assertRaises(json.JSONDecodeError):
            _parse_evaluation("not json at all")

    def test_raises_on_missing_feedback(self):
        no_feedback = json.dumps({
            "voice_alignment": 8.0,
            "factual_rigor": 7.0,
            "format_compliance": 8.0,
            "thematic_alignment": 7.0,
        })
        with self.assertRaises(ValueError):
            _parse_evaluation(no_feedback)

    def test_raises_on_score_out_of_range(self):
        out_of_range = json.dumps({
            "voice_alignment": 11.0,
            "factual_rigor": 7.0,
            "format_compliance": 8.0,
            "thematic_alignment": 7.0,
            "feedback": "ok",
        })
        with self.assertRaises(ValueError):
            _parse_evaluation(out_of_range)


@patch("agents.editor.evaluator.completion")
class TestEvaluate(unittest.TestCase):
    def test_approved_when_all_above_threshold(self, mock_completion):
        mock_completion.return_value = SYNTHETIC_LLM_EVALUATION_APPROVED

        result = evaluate(SYNTHETIC_POST, SYNTHETIC_BRIEF, SYNTHETIC_VOICE, SYNTHETIC_FORMAT_ANALYSIS)

        self.assertEqual(result["decision"], "approved")
        self.assertIn("scores", result)
        self.assertIn("average_score", result)
        self.assertIn("feedback", result)
        for dim in DIMENSIONS:
            self.assertIn(dim, result["scores"])
            self.assertGreaterEqual(result["scores"][dim], VETO_THRESHOLD)

    def test_needs_revision_when_veto(self, mock_completion):
        mock_completion.return_value = SYNTHETIC_LLM_EVALUATION_VETO

        result = evaluate(SYNTHETIC_POST, SYNTHETIC_BRIEF, SYNTHETIC_VOICE, SYNTHETIC_FORMAT_ANALYSIS)

        self.assertEqual(result["decision"], "needs_revision")
        self.assertLess(result["scores"]["factual_rigor"], VETO_THRESHOLD)

    def test_feedback_not_empty(self, mock_completion):
        mock_completion.return_value = SYNTHETIC_LLM_EVALUATION_VETO

        result = evaluate(SYNTHETIC_POST, SYNTHETIC_BRIEF, SYNTHETIC_VOICE, SYNTHETIC_FORMAT_ANALYSIS)

        self.assertTrue(len(result["feedback"]) > 0)

    def test_average_score_calculated(self, mock_completion):
        mock_completion.return_value = SYNTHETIC_LLM_EVALUATION_APPROVED

        result = evaluate(SYNTHETIC_POST, SYNTHETIC_BRIEF, SYNTHETIC_VOICE, SYNTHETIC_FORMAT_ANALYSIS)

        expected = (8.0 + 7.5 + 9.0 + 8.5) / 4
        self.assertAlmostEqual(result["average_score"], expected, places=2)

    def test_works_without_brief(self, mock_completion):
        mock_completion.return_value = SYNTHETIC_LLM_EVALUATION_APPROVED

        result = evaluate(SYNTHETIC_POST, None, SYNTHETIC_VOICE, SYNTHETIC_FORMAT_ANALYSIS)

        self.assertEqual(result["decision"], "approved")
        # Verify the prompt was built (completion was called)
        mock_completion.assert_called_once()

    def test_calls_haiku_model(self, mock_completion):
        mock_completion.return_value = SYNTHETIC_LLM_EVALUATION_APPROVED

        evaluate(SYNTHETIC_POST, SYNTHETIC_BRIEF, SYNTHETIC_VOICE, SYNTHETIC_FORMAT_ANALYSIS)

        call_kwargs = mock_completion.call_args.kwargs
        self.assertEqual(call_kwargs["model"], "anthropic/claude-haiku-4-5-20251001")


if __name__ == "__main__":
    unittest.main()
