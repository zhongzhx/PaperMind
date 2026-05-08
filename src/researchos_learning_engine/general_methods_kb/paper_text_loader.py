"""Load paper text from local files.

Supports .txt, .md (read as UTF-8), and .pdf (basic extraction).
PDF extraction failure is non-fatal — returns empty text.
"""

from __future__ import annotations

from pathlib import Path


def load_text(file_path: str) -> str:
    """Read text content from *file_path*.

    For .txt and .md: read as UTF-8 text.
    For .pdf: attempt extraction via pure-Python fallback.
    """
    p = Path(file_path)
    ext = p.suffix.lower()

    if ext == ".pdf":
        return _load_pdf_text(file_path)

    # .txt / .md
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _load_pdf_text(file_path: str) -> str:
    """Attempt PDF text extraction. Returns empty string on failure."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return _extract_pdf_text_basic(data)
    except Exception:
        return ""


def _extract_pdf_text_basic(data: bytes) -> str:
    """Pure-Python PDF text extractor (no external dependencies).

    Tries optional libraries first (fitz, pypdf), falls back to
    regex-based extraction from raw PDF content.
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

    # Attempt 3: Pure-Python regex fallback
    import re

    text_parts = []
    try:
        raw = data.decode("latin-1", errors="replace")

        # Tj operator
        for m in re.finditer(r"\(([^)]*)\)\s*Tj", raw):
            text_parts.append(_clean_pdf_text(m.group(1)))

        # TJ array
        for m in re.finditer(r"\[([^\]]*)\]\s*TJ", raw):
            for subm in re.finditer(r"\(([^)]*)\)", m.group(1)):
                text_parts.append(_clean_pdf_text(subm.group(1)))

        # ' operator
        for m in re.finditer(r"\(([^)]*)\)\s*'", raw):
            text_parts.append(_clean_pdf_text(m.group(1)))

        if text_parts:
            return "\n".join(text_parts).strip()

        # Last resort: parenthesized text with high alpha ratio
        for m in re.finditer(r"\(([^)]{5,})\)", raw):
            c = m.group(1)
            alpha_ratio = sum(ch.isalpha() for ch in c) / max(len(c), 1)
            if alpha_ratio > 0.4:
                text_parts.append(_clean_pdf_text(c))
    except Exception:
        pass

    return "\n".join(text_parts).strip()


def _clean_pdf_text(part: str) -> str:
    """Clean escape sequences from PDF text."""
    part = part.replace("\\n", "\n")
    part = part.replace("\\r", "\r")
    part = part.replace("\\t", "\t")
    part = part.replace("\\(", "(")
    part = part.replace("\\)", ")")
    part = part.replace("\\\\", "\\")
    return part
