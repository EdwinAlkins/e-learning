"""Extraction de texte depuis documents catalogue (md/txt/csv/pdf/docx)."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import PurePosixPath

from e_learning.application.shared.document_text import DocumentTextExtractor

logger = logging.getLogger("e_learning")

_TEXT_EXTS = frozenset({".md", ".txt", ".csv"})
_PDF_EXTS = frozenset({".pdf"})
_DOCX_EXTS = frozenset({".docx"})


class FilesystemDocumentTextExtractor(DocumentTextExtractor):
    def extract(
        self,
        data: bytes,
        *,
        filename: str,
        mime_type: str | None = None,
    ) -> str | None:
        if not data:
            return None
        ext = PurePosixPath(filename).suffix.lower()
        try:
            if ext in _TEXT_EXTS or (mime_type or "").startswith("text/"):
                return self._decode_text(data)
            if ext in _PDF_EXTS or mime_type == "application/pdf":
                return self._extract_pdf(data)
            if ext in _DOCX_EXTS or mime_type in {
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            }:
                return self._extract_docx(data)
        except Exception:  # noqa: BLE001
            logger.exception("Échec extraction texte document : %s", filename)
            return None
        return None

    @staticmethod
    def _decode_text(data: bytes) -> str | None:
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                text = data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            return None
        cleaned = " ".join(text.split())
        return cleaned or None

    @staticmethod
    def _extract_pdf(data: bytes) -> str | None:
        try:
            from pypdf import PdfReader
        except ImportError:
            logger.warning("pypdf non installé — PDF ignoré pour le RAG")
            return None
        reader = PdfReader(BytesIO(data))
        parts: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                parts.append(page_text)
        cleaned = " ".join(" ".join(parts).split())
        return cleaned or None

    @staticmethod
    def _extract_docx(data: bytes) -> str | None:
        try:
            from docx import Document as DocxDocument
        except ImportError:
            logger.warning("python-docx non installé — DOCX ignoré pour le RAG")
            return None
        document = DocxDocument(BytesIO(data))
        parts = [p.text for p in document.paragraphs if p.text and p.text.strip()]
        cleaned = " ".join(" ".join(parts).split())
        return cleaned or None
