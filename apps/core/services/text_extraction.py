"""PDF text-extraction service.

A thin, framework-agnostic wrapper around pypdf that turns a PDF into plain
text for downstream AI processing. Business logic lives here, not in models
or views, per the service-layer pattern.
"""

from __future__ import annotations

from typing import BinaryIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class TextExtractionError(Exception):
    """Raised when a PDF cannot be read or contains no extractable text."""


def extract_text_from_pdf(source: BinaryIO | str) -> str:
    """Extract plain text from a PDF.

    `source` may be a filesystem path or any binary file-like object
    (including a Django ``FieldFile`` opened in binary mode).

    Raises:
        TextExtractionError: if the file is unreadable, password-protected,
            or has no extractable text layer (e.g. a scanned/image PDF).
    """
    try:
        reader = PdfReader(source)
    except (PdfReadError, OSError, ValueError) as exc:
        raise TextExtractionError(f"Could not read the PDF: {exc}") from exc

    if reader.is_encrypted:
        try:
            # Many PDFs are "encrypted" only with an empty password.
            decrypt_result = reader.decrypt("")
        except Exception as exc:  # noqa: BLE001 - pypdf raises varied types here
            raise TextExtractionError(
                "The PDF is password-protected and cannot be read."
            ) from exc
        if not decrypt_result:
            raise TextExtractionError(
                "The PDF is password-protected and cannot be read."
            )

    pages_text: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        if extracted.strip():
            pages_text.append(extracted.strip())

    text = "\n\n".join(pages_text).strip()

    if not text:
        raise TextExtractionError(
            "No extractable text found. This may be a scanned or image-only PDF."
        )

    return text