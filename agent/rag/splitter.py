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
