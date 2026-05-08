#!/usr/bin/env python3
"""Local demo server for the PaperMind Learning Engine.

Provides a lightweight HTTP API for testing:
  1. High-Impact Paper Learning (learn_high_impact_paper)
  2. PDF Upload & Text Extraction
  3. Project Sleep Cycle (run_sleep_cycle)
  4. Exporting results

Usage:
    PYTHONPATH=src python3 demo_app/server.py
    # Open http://127.0.0.1:8766
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import mimetypes
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Ensure src is on the path
ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = str(ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from researchos_learning_engine.adapters.llm.mock_llm import MockLLMAdapter
from researchos_learning_engine.paper_learning.library_service import (
    learn_high_impact_paper,
)
from researchos_learning_engine.paper_learning.schemas import HighImpactPaperRecord
from researchos_learning_engine.interfaces.python_api import run_sleep_cycle
from researchos_learning_engine.domain.schemas import ConsolidationInput
from researchos_learning_engine.domain.constants import ENGINE_VERSION, SCHEMA_VERSION

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DEMO_DIR = Path(__file__).resolve().parent
STATIC_DIR = DEMO_DIR / "static"
DEMO_EXPORTS_DIR = DEMO_DIR / "exports"

# Reusable mock LLM (no real API calls)
_MOCK_LLM = MockLLMAdapter()

# ---------------------------------------------------------------------------
# PDF Text Extraction (pure Python fallback if no PDF library available)
# ---------------------------------------------------------------------------


def _extract_pdf_text(data: bytes) -> str:
    """Extract text from a PDF byte blob.

    Tries multiple backends in order of preference:
      1. PyMuPDF (fitz)
      2. pypdf
      3. Pure-Python regex-based fallback
    """
    # Attempt 1: PyMuPDF
    try:
        import fitz
        doc = fitz.open(stream=data, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        if text.strip():
            return text.strip()
    except ImportError:
        pass
    except Exception:
        pass

    # Attempt 2: pypdf
    try:
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if text.strip():
            return text.strip()
    except ImportError:
        pass
    except Exception:
        pass

    # Attempt 3: Pure-Python fallback — extract text from PDF content streams
    text = ""
    try:
        text = _basic_pdf_extract(data)
    except Exception:
        pass
    return text.strip() or "（纯文本提取器未找到可提取文本）"


def _basic_pdf_extract(data: bytes) -> str:
    """Extract text from a PDF using basic heuristics (pure Python).

    Does NOT require any external PDF library. Works by scanning the raw
    PDF for text-showing operators (Tj, TJ, ', ") and text between
    parentheses within content streams.

    Limitations: won't handle compressed streams or encoded fonts,
    but catches many text-based academic PDFs.
    """
    text_parts = []
    raw = data.decode("latin-1", errors="replace")

    # 1) Extract from Tj: (text) Tj
    for m in re.finditer(r"\(([^)]*)\)\s*Tj", raw):
        text_parts.append(m.group(1))

    # 2) Extract from TJ arrays: [(text) num (text)] TJ
    for m in re.finditer(r"\[([^\]]*)\]\s*TJ", raw):
        inner = m.group(1)
        for subm in re.finditer(r"\(([^)]*)\)", inner):
            text_parts.append(subm.group(1))

    # 3) Extract from ' (move to next line and show text)
    for m in re.finditer(r"\(([^)]*)\)\s*'", raw):
        text_parts.append(m.group(1))

    # 4) Extract from " (set word/char spacing and show text)
    for m in re.finditer(r"\(([^)]*)\)\s*\"", raw):
        text_parts.append(m.group(1))

    # 5) If still empty, try grabbing any parenthesized text that
    #    looks like natural language (at least 5 chars, no hex)
    if not text_parts:
        for m in re.finditer(r"\(([^)]{5,})\)", raw):
            candidate = m.group(1)
            # Skip lines that look like PDF internals (too many non-alpha)
            alpha_ratio = sum(c.isalpha() for c in candidate) / max(len(candidate), 1)
            if alpha_ratio > 0.4:
                text_parts.append(candidate)

    # Clean up escape sequences
    result = []
    for part in text_parts:
        part = part.replace("\\n", "\n")
        part = part.replace("\\r", "\r")
        part = part.replace("\\t", "\t")
        part = part.replace("\\(", "(")
        part = part.replace("\\)", ")")
        part = part.replace("\\\\", "\\")
        # Remove isolated backslashes before regular characters
        part = re.sub(r"\\([^nrt\\()])", r"\1", part)
        result.append(part)

    return "\n".join(result).strip()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _json_bytes(obj) -> bytes:
    return json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")


# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------


class DemoHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the demo API and static files."""

    # Silence default logging per-request
    def log_message(self, format, *args):
        pass

    def _send_json(self, status: int, data) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(_json_bytes(data))

    def _send_error_json(self, status: int, message: str) -> None:
        self._send_json(status, {"error": message})

    def _read_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw)

    def _serve_static(self, url_path: str) -> None:
        if url_path == "/" or url_path == "":
            url_path = "/index.html"
        if url_path.startswith("/static/"):
            rel = url_path[len("/static/"):]
        else:
            rel = url_path.lstrip("/")
        file_path = STATIC_DIR / rel
        if not file_path.exists() or not file_path.is_file():
            self._send_error_json(404, f"File not found: {url_path}")
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        if content_type is None:
            content_type = "application/octet-stream"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        with open(file_path, "rb") as f:
            self.wfile.write(f.read())

    # ------------------------------------------------------------------
    # Route dispatch
    # ------------------------------------------------------------------

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = self._parse_url()
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/health":
            self._handle_health()
        else:
            self._serve_static(path)

    def do_POST(self):
        parsed = self._parse_url()
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/paper/learn":
            self._handle_paper_learn()
        elif path == "/api/paper/upload-pdf":
            self._handle_paper_upload_pdf()
        elif path == "/api/sleep-cycle":
            self._handle_sleep_cycle()
        elif path == "/api/export":
            self._handle_export()
        else:
            self._send_error_json(404, "Not found")

    def _parse_url(self):
        from urllib.parse import urlparse
        return urlparse(self.path)

    # ------------------------------------------------------------------
    # API handlers
    # ------------------------------------------------------------------

    def _handle_health(self):
        self._send_json(200, {
            "status": "ok",
            "engine_version": ENGINE_VERSION,
            "schema_version": SCHEMA_VERSION,
        })

    def _handle_paper_learn(self):
        try:
            body = self._read_body()
        except json.JSONDecodeError as e:
            self._send_error_json(400, f"Invalid JSON body: {e}")
            return

        paper_dict = body.get("paper")
        if not paper_dict:
            self._send_error_json(400, "Missing 'paper' field")
            return

        project_context = body.get("project_context", {})
        project_id = project_context.get("project_id", "demo")
        project_description = project_context.get("project_description", "")

        try:
            paper = HighImpactPaperRecord.from_dict(paper_dict)
            result = learn_high_impact_paper(
                paper=paper,
                llm=_MOCK_LLM,
                project_id=project_id,
                project_description=project_description,
            )
            self._send_json(200, result.to_dict())
        except Exception as e:
            self._send_error_json(500, f"Paper learning failed: {e}")

    def _handle_paper_upload_pdf(self):
        try:
            body = self._read_body()
        except json.JSONDecodeError as e:
            self._send_error_json(400, f"Invalid JSON body: {e}")
            return

        filename = body.get("filename", "uploaded.pdf")
        data_b64 = body.get("data", "")
        if not data_b64:
            self._send_error_json(400, "Missing 'data' field (base64-encoded PDF)")
            return

        try:
            pdf_bytes = base64.b64decode(data_b64)
            full_text = _extract_pdf_text(pdf_bytes)
        except Exception as e:
            self._send_error_json(500, f"PDF extraction failed: {e}")
            return

        # Truncate extremely long texts
        if len(full_text) > 500000:
            full_text = full_text[:500000] + "\n\n[文本截断 — PDF 超过 500K 字符]"

        paper_id = f"pdf_{uuid.uuid4().hex[:12]}"
        title = filename.replace(".pdf", "").replace("_", " ").replace("-", " ").strip()

        self._send_json(200, {
            "paper_id": paper_id,
            "title": title,
            "full_text": full_text,
            "text_length": len(full_text),
            "authors": [],
        })

    def _handle_sleep_cycle(self):
        try:
            body = self._read_body()
        except json.JSONDecodeError as e:
            self._send_error_json(400, f"Invalid JSON body: {e}")
            return

        try:
            input_data = ConsolidationInput.from_dict(body)
            result = run_sleep_cycle(input_data)
            self._send_json(200, result.to_dict())
        except Exception as e:
            self._send_error_json(500, f"Sleep cycle failed: {e}")

    def _handle_export(self):
        try:
            body = self._read_body()
        except json.JSONDecodeError as e:
            self._send_error_json(400, f"Invalid JSON body: {e}")
            return

        name = body.get("name", "demo_export.json")
        name = os.path.basename(name)
        if not name.endswith(".json"):
            name += ".json"

        content = body.get("content", body)

        os.makedirs(DEMO_EXPORTS_DIR, exist_ok=True)
        out_path = DEMO_EXPORTS_DIR / name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

        self._send_json(200, {
            "saved": True,
            "path": str(out_path.relative_to(DEMO_DIR)),
        })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    port = int(os.environ.get("DEMO_PORT", "8766"))
    host = os.environ.get("DEMO_HOST", "127.0.0.1")
    server = HTTPServer((host, port), DemoHandler)
    print(f"PaperMind Learning Engine · Demo Server")
    print(f"Local: http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
