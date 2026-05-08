"""Tests for the demo_app HTTP server handler logic.

Tests each API handler method directly by instantiating the
DemoHandler without binding to a socket.
"""

from __future__ import annotations

import http.client
import io
import json
import sys
import unittest
from pathlib import Path

# Make the server module importable
_DEMO_DIR = str(Path(__file__).resolve().parent.parent / "demo_app")
if _DEMO_DIR not in sys.path:
    sys.path.insert(0, _DEMO_DIR)

from server import DemoHandler  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


class TestDemoHandlerDirect(unittest.TestCase):
    """Test handler methods directly — no socket binding required."""

    def setUp(self):
        """Create a lightweight DemoHandler without a live socket."""
        h = DemoHandler.__new__(DemoHandler)
        h.command = "GET"
        h.path = "/"
        h.request_version = "HTTP/1.1"
        h.requestline = "GET / HTTP/1.1"
        h.client_address = ("127.0.0.1", 0)
        h.server = None
        h.close_connection = True
        h.headers = http.client.HTTPMessage()
        h.rfile = io.BytesIO(b"")
        h.wfile = io.BytesIO()
        h.log_message = lambda *a: None
        h.protocol_version = "HTTP/1.1"
        # Capture JSON responses via _send_json override
        self._last_status: int | None = None
        self._last_data: dict | None = None

        def _capture_send_json(status, data):
            self._last_status = status
            self._last_data = data

        h._send_json = _capture_send_json
        # Simplify _send_error_json to use the same capture
        h._send_error_json = lambda status, msg: _capture_send_json(status, {"error": msg})

        self.handler = h

    def _set_body(self, data: dict):
        """Set the request body for POST handlers."""
        raw = json.dumps(data).encode("utf-8")
        self.handler.rfile = io.BytesIO(raw)
        self.handler.headers.add_header("Content-Length", str(len(raw)))
        self.handler.headers.add_header("Content-Type", "application/json")

    def _make_minimal_paper(self) -> dict:
        """Return a minimal inline paper dict for testing."""
        return {
            "paper_id": "test_inline_001",
            "title": "Inline Test Paper",
            "full_text": (
                "Abstract\n\nThis is a test abstract.\n\n"
                "Introduction\n\nBackground and hypothesis.\n\n"
                "Methods\n\nCell culture and treatments.\n\n"
                "Results\n\nKey findings.\n\n"
                "Discussion\n\nInterpretation.\n\n"
                "Conclusion\n\nSummary.\n\n"
            ),
            "authors": ["Author A"],
            "journal": "Journal of Testing",
            "year": 2024,
        }

    # ------------------------------------------------------------------
    # GET /api/health
    # ------------------------------------------------------------------

    def test_health_returns_ok(self):
        self.handler._handle_health()
        self.assertEqual(self._last_status, 200)
        self.assertEqual(self._last_data["status"], "ok")
        self.assertIn("engine_version", self._last_data)
        self.assertIn("schema_version", self._last_data)

    # ------------------------------------------------------------------
    # POST /api/paper/learn
    # ------------------------------------------------------------------

    def test_paper_learn_with_inline_paper(self):
        paper = self._make_minimal_paper()
        self._set_body({
            "paper": paper,
            "project_context": {
                "project_id": "test_paper_learn",
                "project_description": "Example project for testing",
            },
        })
        self.handler._handle_paper_learn()
        self.assertEqual(self._last_status, 200, f"Error: {self._last_data}")
        data = self._last_data
        self.assertIn("paper_id", data)
        self.assertIn("quality_score", data)
        self.assertIn("experiment_design_patterns", data)
        self.assertIn("mechanism_patterns", data)
        self.assertIn("figure_logic_patterns", data)
        self.assertIn("writing_patterns", data)
        self.assertIn("reusable_insights", data)
        # With MockLLM, patterns should be non-empty
        self.assertGreater(len(data["experiment_design_patterns"]), 0)
        self.assertGreater(len(data["reusable_insights"]), 0)
        self.assertGreater(len(data["mechanism_patterns"]), 0)
        # Quality score in range
        self.assertGreaterEqual(data["quality_score"], 0.0)
        self.assertLessEqual(data["quality_score"], 1.0)

    def test_paper_learn_missing_paper_field(self):
        self._set_body({"project_context": {}})
        self.handler._handle_paper_learn()
        self.assertEqual(self._last_status, 400)
        self.assertIn("error", self._last_data)

    def test_paper_learn_invalid_body_json(self):
        self.handler.rfile = io.BytesIO(b"not json at all")
        self.handler.headers.add_header("Content-Length", "14")
        self.handler._handle_paper_learn()
        self.assertEqual(self._last_status, 400)
        self.assertIn("error", self._last_data)

    # ------------------------------------------------------------------
    # POST /api/sleep-cycle
    # ------------------------------------------------------------------

    def test_sleep_cycle_with_minimal_input(self):
        self._set_body({"project_id": "minimal_test"})
        self.handler._handle_sleep_cycle()
        self.assertEqual(self._last_status, 200, f"Error: {self._last_data}")
        data = self._last_data
        self.assertEqual(data["project_id"], "minimal_test")

    def test_sleep_cycle_returns_expected_fields(self):
        self._set_body({"project_id": "test_sleep"})
        self.handler._handle_sleep_cycle()
        self.assertEqual(self._last_status, 200, f"Error: {self._last_data}")
        data = self._last_data
        self.assertIn("project_id", data)
        self.assertIn("promoted_memories", data)
        self.assertIn("archived_memories", data)
        self.assertIn("superseded_memories", data)
        self.assertIn("new_research_patterns", data)
        self.assertIn("new_evidence_edges", data)
        self.assertIn("updated_project_summary", data)
        self.assertIn("recommended_literature_queries", data)
        self.assertIn("warnings", data)
        self.assertIn("processing_log", data)
        self.assertIn("schema_version", data)
        self.assertIn("engine_version", data)

    # ------------------------------------------------------------------
    # POST /api/export
    # ------------------------------------------------------------------

    def test_export_saves_and_returns_path(self):
        self._set_body({
            "name": "test_export.json",
            "content": {"test": True, "value": 42},
        })
        self.handler._handle_export()
        self.assertEqual(self._last_status, 200)
        self.assertTrue(self._last_data["saved"])
        self.assertIn("path", self._last_data)
        # Verify file was written relative to demo_app/ and clean up
        demo_dir = ROOT / "demo_app"
        written_path = demo_dir / self._last_data["path"]
        self.assertTrue(written_path.exists())
        written_path.unlink()

    def test_export_without_name(self):
        self._set_body({"content": {"a": 1}})
        self.handler._handle_export()
        self.assertEqual(self._last_status, 200)
        self.assertTrue(self._last_data["saved"])
        # Clean up
        demo_dir = ROOT / "demo_app"
        written_path = demo_dir / self._last_data["path"]
        if written_path.exists():
            written_path.unlink()

    # ------------------------------------------------------------------
    # Static file serving
    # ------------------------------------------------------------------

    def test_serve_index_html(self):
        self.handler.path = "/"
        self.handler._serve_static("/")
        wfile_value = self.handler.wfile.getvalue()
        # Should contain HTML with PaperMind
        self.assertIn(b"PaperMind", wfile_value)
        self.assertIn(b"text/html", wfile_value)

    def test_serve_app_js(self):
        self.handler.path = "/static/app.js"
        self.handler._serve_static("/static/app.js")
        wfile_value = self.handler.wfile.getvalue()
        self.assertIn(b"apiGet", wfile_value)

    def test_serve_styles_css(self):
        self.handler.path = "/static/styles.css"
        self.handler._serve_static("/static/styles.css")
        wfile_value = self.handler.wfile.getvalue()
        self.assertIn(b"--c-primary", wfile_value)

    def test_serve_missing_file(self):
        self.handler._serve_static("/nonexistent.file")
        self.assertEqual(self._last_status, 404)

    # ------------------------------------------------------------------
    # Route dispatch
    # ------------------------------------------------------------------

    def test_do_get_api_health(self):
        self.handler.command = "GET"
        self.handler.path = "/api/health"
        self.handler.do_GET()
        self.assertEqual(self._last_status, 200)
        self.assertEqual(self._last_data["status"], "ok")

    def test_do_post_unknown_route(self):
        self.handler.command = "POST"
        self.handler.path = "/api/unknown"
        self.handler.do_POST()
        self.assertEqual(self._last_status, 404)
        self.assertIn("error", self._last_data)


class TestServerUtilities(unittest.TestCase):
    """Test server helper functions without handler setup."""

    def test_health_response_format(self):
        """Verify the health response has expected version fields."""
        from server import ENGINE_VERSION, SCHEMA_VERSION
        self.assertIsInstance(ENGINE_VERSION, str)
        self.assertIsInstance(SCHEMA_VERSION, str)
        self.assertGreater(len(ENGINE_VERSION), 0)
        self.assertGreater(len(SCHEMA_VERSION), 0)
