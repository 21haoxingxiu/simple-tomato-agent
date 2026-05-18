"""文本分块与文档解析。"""
from __future__ import annotations

import io
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120


def parse_file(filename: str, content: bytes) -> str:
    """支持 pdf / docx / md / txt / html;尽力 best-effort 解析。"""
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise ValueError(f"PDF parse error: {exc}") from exc

    if suffix == ".docx":
        try:
            from docx import Document as DocxDocument  # type: ignore

            doc = DocxDocument(io.BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as exc:
            raise ValueError(f"DOCX parse error: {exc}") from exc

    if suffix in (".html", ".htm"):
        try:
            from bs4 import BeautifulSoup  # type: ignore

            soup = BeautifulSoup(content, "html.parser")
            return soup.get_text("\n")
        except Exception:
            return content.decode("utf-8", errors="replace")

    return content.decode("utf-8", errors="replace")


def split_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """递归字符切分;保留段落优先。"""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "!", "?", ".", " ", ""],
    )
    chunks = [c.strip() for c in splitter.split_text(text) if c and c.strip()]
    return chunks


_WORD_RE = re.compile(r"\S+")


def estimate_tokens(text: str) -> int:
    return len(_WORD_RE.findall(text))
