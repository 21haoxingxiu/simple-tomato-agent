"""文本分块与文档解析。"""
from __future__ import annotations

import io
import logging
import os
import re
from pathlib import Path
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120


class ParsingLevel(str, Enum):
    """文档解析级别"""
    BASIC = "basic"  # 基础文本提取
    STANDARD = "standard"  # 标准（现有方式）
    ENHANCED = "enhanced"  # 增强（使用 DeepDoc）


def parse_file(
    filename: str,
    content: bytes,
    parsing_level: ParsingLevel = ParsingLevel.STANDARD,
    enable_ocr: bool = False,
    enable_layout: bool = False,
    enable_table_structure: bool = False,
    **kwargs
) -> str:
    """
    支持多种文档格式解析，可选择使用 DeepDoc 增强解析。

    Args:
        filename: 文件名
        content: 文件内容（字节）
        parsing_level: 解析级别（basic/standard/enhanced）
        enable_ocr: 是否启用 OCR（自动用于 enhanced 级别）
        enable_layout: 是否启用布局识别
        enable_table_structure: 是否启用表格结构识别
        **kwargs: 额外参数

    Returns:
        解析后的文本内容
    """
    suffix = Path(filename).suffix.lower()

    # Check if DeepDoc is enabled
    use_deepdoc = (
        parsing_level == ParsingLevel.ENHANCED or
        enable_ocr or
        enable_layout or
        enable_table_structure
    )

    if use_deepdoc and suffix in [".pdf", ".png", ".jpg", ".jpeg"]:
        # Use DeepDoc enhanced parsing
        try:
            return _parse_with_deepdoc(
                filename,
                content,
                enable_ocr=enable_ocr or parsing_level == ParsingLevel.ENHANCED,
                enable_layout=enable_layout or parsing_level == ParsingLevel.ENHANCED,
                enable_table_structure=enable_table_structure or parsing_level == ParsingLevel.ENHANCED,
                **kwargs
            )
        except Exception as e:
            logger.warning(f"DeepDoc parsing failed, falling back to standard: {e}")
            # Fall through to standard parsing

    # Standard parsing (existing logic)
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


def _parse_with_deepdoc(
    filename: str,
    content: bytes,
    enable_ocr: bool = False,
    enable_layout: bool = False,
    enable_table_structure: bool = False,
    **kwargs
) -> str:
    """
    使用 DeepDoc 进行增强解析

    Args:
        filename: 文件名
        content: 文件内容
        enable_ocr: 是否启用 OCR
        enable_layout: 是否启用布局识别
        enable_table_structure: 是否启用表格结构识别

    Returns:
        解析后的文本内容
    """
    import tempfile

    suffix = Path(filename).suffix.lower()

    # Save content to temporary file
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(content)

    try:
        # Import DeepDoc parsers
        from deepdoc.parser.pdf_parser import PDFParser
        from deepdoc.parser.image_parser import ImageParser
        from deepdoc.parser.base import ParsingLevel

        # Determine parser
        if suffix == ".pdf":
            parser = PDFParser(
                parsing_level=ParsingLevel.FULL if enable_ocr else ParsingLevel.STANDARD
            )
        elif suffix in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
            parser = ImageParser()
        else:
            raise ValueError(f"Unsupported format for DeepDoc: {suffix}")

        # Parse document
        result = parser.parse(tmp_path)

        # Extract text content
        # For enhanced parsing, we might want to structure the output differently
        if enable_layout or enable_table_structure:
            # Include structured elements
            text_parts = []

            for element in result.elements:
                if element.type == "table" and enable_table_structure:
                    # Include both natural language and markdown versions
                    table_text = element.content
                    if element.metadata.get("markdown"):
                        table_text += f"\n\n表格（Markdown格式）:\n{element.metadata['markdown']}"
                    text_parts.append(table_text)
                else:
                    text_parts.append(element.content)

            return "\n\n".join(text_parts)
        else:
            return result.text_content

    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


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
