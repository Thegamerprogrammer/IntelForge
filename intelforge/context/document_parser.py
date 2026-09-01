from __future__ import annotations

from pathlib import Path

from ..core.errors import ValidationError


class DocumentParser:
    def extract(self, path: str) -> str:
        file = Path(path)
        if not file.is_file():
            raise ValidationError(f"Background guide does not exist: {path}")
        suffix = file.suffix.casefold()
        if suffix == ".txt":
            return file.read_text(encoding="utf-8")
        if suffix == ".pdf":
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise ValidationError("PDF support requires `pip install intelforge[documents]`.") from exc
            return "\n".join(page.extract_text() or "" for page in PdfReader(str(file)).pages)
        if suffix == ".docx":
            try:
                from docx import Document
            except ImportError as exc:
                raise ValidationError("DOCX support requires `pip install intelforge[documents]`.") from exc
            return "\n".join(p.text for p in Document(str(file)).paragraphs)
        raise ValidationError("Background guides must be .txt, .pdf, or .docx")
