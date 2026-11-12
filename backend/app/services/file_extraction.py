"""Extract plain text from an uploaded CV/JD file."""

from __future__ import annotations

import io

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


class UnsupportedFileTypeError(Exception):
    pass


def extract_text(filename: str, content: bytes) -> str:
    lower = filename.lower()

    if lower.endswith(".pdf"):
        from pypdf import PdfReader  # lazy import

        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()

    if lower.endswith(".txt") or lower.endswith(".md"):
        return content.decode("utf-8", errors="replace").strip()

    raise UnsupportedFileTypeError(
        f"Unsupported file type for '{filename}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
    )
