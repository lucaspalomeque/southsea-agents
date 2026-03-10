"""Tests para el Pipeline Orchestrator (scripts/run_pipeline.py)."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.run_pipeline import (
    PIPELINE,
    AgentResult,
    generate_report,
    rotate_logs,
    run_agent_with_metrics,
    run_pipeline,
    setup_logging,
)


def _mock_factory(return_value=None, side_effect=None):
    """Crea una factory que devuelve un agente mock con run()."""
    agent = MagicMock()
    if side_effect:
        agent.run.side_effect = side_effect
    else:
        agent.run.return_value = return_value or []
    factory = MagicMock(return_value=agent)
    return factory


class TestRunAgentWithMetrics(unittest.TestCase):
    """Tests para el wrapper run_agent_with_metrics."""

    @patch("scripts.run_pipeline.timeout")
    def test_agent_success(self, mock_timeout):
        mock_timeout.return_value.__enter__ = MagicMock()
        mock_timeout.return_value.__exit__ = MagicMock(return_value=False)
        factory = _mock_factory(return_value=[{"id": "1"}, {"id": "2"}])

        result = run_agent_with_metrics("scout", factory, timeout_seconds=60, retry_backoff=0)

        self.assertEqual(result.agent_name, "scout")
        self.assertEqual(result.items_success, 2)
        self.assertEqual(result.items_error, 0)
        self.assertEqual(result.status, "ok")
        self.assertGreater(result.duration_seconds, 0)
        self.assertEqual(result.errors, [])

    @patch("scripts.run_pipeline.timeout")
    def test_agent_empty_result(self, mock_timeout):
        mock_timeout.return_value.__enter__ = MagicMock()
        mock_timeout.return_value.__exit__ = MagicMock(return_value=False)
        factory = _mock_factory(return_value=[])

        result = run_agent_with_metrics("analyst", factory, timeout_seconds=60, retry_backoff=0)

        self.assertEqual(result.items_success, 0)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.errors, [])

    @patch("scripts.run_pipeline.time")
    @patch("scripts.run_pipeline.timeout")
    def test_agent_fails_then_retry_succeeds(self, mock_timeout, mock_time):
        mock_timeout.return_value.__enter__ = MagicMock()
        mock_timeout.return_value.__exit__ = MagicMock(return_value=False)
        mock_time.time.side_effect = [0.0, 1.0, 31.0, 32.0]
        mock_time.sleep = MagicMock()

        factory = _mock_factory(side_effect=[
            RuntimeError("connection lost"),
            [{"id": "1"}],
        ])

        result = run_agent_with_metrics("writer", factory, timeout_seconds=60, retry_backoff=30)

        self.assertEqual(result.status, "retry_ok")
        self.assertEqual(result.items_success, 1)
        mock_time.sleep.assert_called_once_with(30)

    @patch("scripts.run_pipeline.time")
    @patch("scripts.run_pipeline.timeout")
    def test_agent_fails_both_attempts(self, mock_timeout, mock_time):
        mock_timeout.return_value.__enter__ = MagicMock()
        mock_timeout.return_value.__exit__ = MagicMock(return_value=False)
        mock_time.time.side_effect = [0.0, 1.0, 31.0, 32.0]
        mock_time.sleep = MagicMock()

        factory = _mock_factory(side_effect=[
            RuntimeError("first fail"),
            RuntimeError("second fail"),
        ])

        result = run_agent_with_metrics("editor", factory, timeout_seconds=60, retry_backoff=30)

        self.assertEqual(result.status, "retry_failed")
        self.assertEqual(result.items_error, 1)
        self.assertEqual(result.items_success, 0)
        self.assertEqual(len(result.errors), 2)

    @patch("scripts.run_pipeline.time")
    @patch("scripts.run_pipeline.timeout")
    def test_timeout_triggers_retry(self, mock_timeout, mock_time):
        mock_timeout.return_value.__enter__ = MagicMock()
        mock_timeout.return_value.__exit__ = MagicMock(return_value=False)
        mock_time.time.side_effect = [0.0, 300.0, 330.0, 335.0]
        mock_time.sleep = MagicMock()

        factory = _mock_factory(side_effect=[
            TimeoutError("Timeout after 300s"),
            [{"id": "1"}, {"id": "2"}, {"id": "3"}],
        ])

        result = run_agent_with_metrics("analyst", factory, timeout_seconds=300, retry_backoff=30)

        self.assertEqual(result.status, "retry_ok")
        self.assertEqual(result.items_success, 3)

    @patch("scripts.run_pipeline.time")
    @patch("scripts.run_pipeline.timeout")
    def test_retry_backoff_is_respected(self, mock_timeout, mock_time):
        mock_timeout.return_value.__enter__ = MagicMock()
        mock_timeout.return_value.__exit__ = MagicMock(return_value=False)
        mock_time.time.side_effect = [0.0, 1.0, 31.0, 32.0]
        mock_time.sleep = MagicMock()

        factory = _mock_factory(side_effect=[
            RuntimeError("fail"),
            [],
        ])

        run_agent_with_metrics("scout", factory, timeout_seconds=60, retry_backoff=30)

        mock_time.sleep.assert_called_once_with(30)


class TestSetupLogging(unittest.TestCase):
    """Tests para setup_logging."""

    def test_log_file_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = setup_logging(log_dir=Path(tmp))
            self.assertTrue(log_path.exists())
            self.assertTrue(log_path.name.startswith("pipeline_"))
            self.assertTrue(log_path.name.endswith(".log"))

    def test_log_dir_created_if_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            nested = Path(tmp) / "subdir" / "logs"
            log_path = setup_logging(log_dir=nested)
            self.assertTrue(nested.exists())
            self.assertTrue(log_path.exists())


class TestRotateLogs(unittest.TestCase):
    """Tests para rotate_logs."""

    def test_rotation_deletes_oldest(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Crear 32 archivos con timestamps distintos
            for i in range(32):
                f = tmp_path / f"pipeline_2026-03-{i:02d}_00-00-00.log"
                f.write_text(f"log {i}")

            rotate_logs(log_dir=tmp_path, max_files=30)

            remaining = list(tmp_path.glob("pipeline_*.log"))
            self.assertEqual(len(remaining), 30)

    def test_rotation_noop_under_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for i in range(5):
                f = tmp_path / f"pipeline_2026-03-0{i}_00-00-00.log"
                f.write_text(f"log {i}")

            rotate_logs(log_dir=tmp_path, max_files=30)

            remaining = list(tmp_path.glob("pipeline_*.log"))
            self.assertEqual(len(remaining), 5)


class TestGenerateReport(unittest.TestCase):
    """Tests para generate_report."""

    def test_report_all_ok(self):
        results = [
            AgentResult("scout", items_success=8, status="ok", duration_seconds=15.0),
            AgentResult("analyst", items_success=6, status="ok", duration_seconds=120.0),
            AgentResult("writer", items_success=5, status="ok", duration_seconds=90.0),
            AgentResult("editor", items_success=5, status="ok", duration_seconds=45.0),
        ]
        start = datetime(2026, 3, 9, 12, 0, 0)
        end = datetime(2026, 3, 9, 12, 14, 32)

        report = generate_report(results, start, end)

        self.assertIn("PIPELINE REPORT", report)
        self.assertIn("Scout", report)
        self.assertIn("8 processed", report)
        self.assertIn("5 processed", report)
        self.assertIn("14m 32s", report)
        self.assertIn("OK", report)
        self.assertIn("24 items through pipeline", report)

    def test_report_pipeline_empty(self):
        results = [
            AgentResult("scout", items_success=0, status="ok"),
            AgentResult("analyst", items_success=0, status="ok"),
            AgentResult("writer", items_success=0, status="ok"),
            AgentResult("editor", items_success=0, status="ok"),
        ]
        start = datetime(2026, 3, 9, 12, 0, 0)
        end = datetime(2026, 3, 9, 12, 0, 5)

        report = generate_report(results, start, end)

        self.assertIn("pipeline empty", report)

    def test_report_partial_failure(self):
        results = [
            AgentResult("scout", items_error=1, errors=["connection refused"], status="retry_failed"),
            AgentResult("analyst", items_success=3, status="ok"),
            AgentResult("writer", items_success=3, status="ok"),
            AgentResult("editor", items_success=3, status="ok"),
        ]
        start = datetime(2026, 3, 9, 12, 0, 0)
        end = datetime(2026, 3, 9, 12, 10, 0)

        report = generate_report(results, start, end)

        self.assertIn("PARTIAL", report)
        self.assertIn("FAILED", report)
        self.assertIn("connection refused", report)

    def test_smoke_test_report_has_label(self):
        results = [AgentResult("scout", items_success=1, status="ok")]
        start = datetime(2026, 3, 9, 12, 0, 0)
        end = datetime(2026, 3, 9, 12, 0, 30)

        report = generate_report(results, start, end, smoke_test=True)

        self.assertIn("SMOKE TEST", report)
        self.assertIn("PIPELINE REPORT", report)

    def test_smoke_test_report_normal_has_no_label(self):
        results = [AgentResult("scout", items_success=1, status="ok")]
        start = datetime(2026, 3, 9, 12, 0, 0)
        end = datetime(2026, 3, 9, 12, 0, 30)

        report = generate_report(results, start, end, smoke_test=False)

        self.assertNotIn("SMOKE TEST", report)

    def test_report_retry_ok_noted(self):
        results = [
            AgentResult("scout", items_success=5, status="retry_ok"),
        ]
        start = datetime(2026, 3, 9, 12, 0, 0)
        end = datetime(2026, 3, 9, 12, 1, 0)

        report = generate_report(results, start, end)

        self.assertIn("after retry", report)


class TestRunPipeline(unittest.TestCase):
    """Tests de integración para run_pipeline."""

    @patch("scripts.run_pipeline.PIPELINE")
    @patch("scripts.run_pipeline.setup_logging")
    @patch("scripts.run_pipeline.rotate_logs")
    @patch("scripts.run_pipeline.timeout")
    def test_full_pipeline_all_succeed(self, mock_timeout, mock_rotate, mock_setup, mock_pipeline):
        mock_timeout.return_value.__enter__ = MagicMock()
        mock_timeout.return_value.__exit__ = MagicMock(return_value=False)
        mock_setup.return_value = Path("/tmp/test.log")

        mock_pipeline.__iter__ = MagicMock(return_value=iter([
            ("scout", _mock_factory([{"id": "1"}, {"id": "2"}])),
            ("analyst", _mock_factory([{"id": "a"}])),
            ("writer", _mock_factory([{"id": "w"}])),
            ("editor", _mock_factory([{"id": "e"}])),
        ]))

        results = run_pipeline()

        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].agent_name, "scout")
        self.assertEqual(results[0].items_success, 2)
        self.assertEqual(results[1].items_success, 1)
        self.assertEqual(results[2].items_success, 1)
        self.assertEqual(results[3].items_success, 1)
        for r in results:
            self.assertEqual(r.status, "ok")

    @patch("scripts.run_pipeline.PIPELINE")
    @patch("scripts.run_pipeline.setup_logging")
    @patch("scripts.run_pipeline.rotate_logs")
    @patch("scripts.run_pipeline.time")
    @patch("scripts.run_pipeline.timeout")
    def test_scout_fails_others_continue(self, mock_timeout, mock_time, mock_rotate, mock_setup, mock_pipeline):
        mock_timeout.return_value.__enter__ = MagicMock()
        mock_timeout.return_value.__exit__ = MagicMock(return_value=False)
        mock_time.time.side_effect = [0, 1, 31, 32] * 4  # enough for all agents
        mock_time.sleep = MagicMock()
        mock_setup.return_value = Path("/tmp/test.log")

        scout_factory = _mock_factory(side_effect=[
            RuntimeError("scout crash"),
            RuntimeError("scout crash again"),
        ])

        mock_pipeline.__iter__ = MagicMock(return_value=iter([
            ("scout", scout_factory),
            ("analyst", _mock_factory([{"id": "a"}])),
            ("writer", _mock_factory([{"id": "w"}])),
            ("editor", _mock_factory([{"id": "e"}])),
        ]))

        results = run_pipeline()

        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].status, "retry_failed")
        self.assertEqual(results[0].items_error, 1)
        # Los otros 3 corrieron OK
        for r in results[1:]:
            self.assertEqual(r.status, "ok")

    @patch("scripts.run_pipeline.PIPELINE")
    @patch("scripts.run_pipeline.setup_logging")
    @patch("scripts.run_pipeline.rotate_logs")
    @patch("scripts.run_pipeline.timeout")
    def test_pipeline_empty_no_errors(self, mock_timeout, mock_rotate, mock_setup, mock_pipeline):
        mock_timeout.return_value.__enter__ = MagicMock()
        mock_timeout.return_value.__exit__ = MagicMock(return_value=False)
        mock_setup.return_value = Path("/tmp/test.log")

        mock_pipeline.__iter__ = MagicMock(return_value=iter([
            ("scout", _mock_factory([])),
            ("analyst", _mock_factory([])),
            ("writer", _mock_factory([])),
            ("editor", _mock_factory([])),
        ]))

        results = run_pipeline()

        self.assertEqual(len(results), 4)
        for r in results:
            self.assertEqual(r.status, "ok")
            self.assertEqual(r.items_success, 0)
            self.assertEqual(r.errors, [])


if __name__ == "__main__":
    unittest.main()
