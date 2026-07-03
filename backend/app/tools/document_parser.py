"""Document parsing utilities for PDF and DOCX resumes.

Pure functions with no LLM dependency so they are fast and unit-testable. The
LLM-based structuring happens later in the Resume Analysis Agent; here we only
extract raw text reliably.
"""
from __future__ import annotations

import io
import re
import unicodedata
from pathlib import Path

# Glyphs that PDF text extraction commonly emits in place of icon fonts
# (FontAwesome etc.) used by LaTeX resume templates. They carry no textual
# meaning, so we drop them to keep the raw text clean for the LLM.
_ICON_JUNK = "♂♀¶⌢⌣⎙⏧"


def _clean_text(text: str) -> str:
    """Strip icon-font artifacts and control chars from extracted text.

    Deliberately conservative: we only remove characters that are clearly
    non-textual (Private Use Area glyphs, control chars, and a few symbol
    substitutes from icon fonts). We do NOT try to reconstruct mangled words
    (e.g. FontAwesome ligatures) because the glyph→letter mapping is
    font-specific and guessing risks deleting real content like emails. The
    Resume Analysis Agent's LLM reliably reads through the residual noise.
    """
    if not text:
        return ""
    out = []
    for ch in text:
        cp = ord(ch)
        # Drop Unicode Private Use Area code points (where icon fonts live).
        if 0xE000 <= cp <= 0xF8FF or 0xF0000 <= cp <= 0xFFFFD or 0x100000 <= cp <= 0x10FFFD:
            continue
        # Remove control chars except common whitespace.
        if unicodedata.category(ch) == "Cc" and ch not in "\n\r\t":
            continue
        out.append(ch)
    text = "".join(out)
    # Remove leftover icon glyph substitutes.
    text = text.translate({ord(c): None for c in _ICON_JUNK})
    # Collapse runs of spaces introduced by the removals.
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def extract_text(filename: str, data: bytes) -> str:
    """Dispatch on file extension and return best-effort plain text."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return _clean_text(_extract_pdf(data))
    if suffix in (".docx", ".doc"):
        return _clean_text(_extract_docx(data))
    if suffix in (".txt", ".md"):
        return _clean_text(data.decode("utf-8", errors="ignore"))
    raise ValueError(f"Unsupported resume type: {suffix}")


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


def _extract_docx(data: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs).strip()
