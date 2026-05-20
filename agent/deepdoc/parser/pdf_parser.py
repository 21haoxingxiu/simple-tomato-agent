"""
Enhanced PDF Parser

Parses PDF documents with OCR, layout recognition, and table structure detection.
"""

import time
import logging
from typing import List, Optional, Dict, Any
import os

from .base import BaseParser, ParsedDocument, ParsedElement, ParsingLevel

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """Enhanced PDF parser with DeepDoc capabilities"""

    def __init__(
        self,
        parsing_level: ParsingLevel = ParsingLevel.STANDARD,
        **kwargs
    ):
        """
        Initialize PDF parser

        Args:
            parsing_level: Parsing intensity level
            **kwargs: Additional parameters
        """
        super().__init__(parsing_level, **kwargs)

        # Lazy-loaded components
        self._ocr_selector = None
        self._layout_recognizer = None
        self._table_recognizer = None

    def parse(self, file_path: str) -> ParsedDocument:
        """
        Parse a PDF file

        Args:
            file_path: Path to the PDF file

        Returns:
            ParsedDocument with parsed elements
        """
        start_time = time.time()

        try:
            import fitz  # PyMuPDF

            # Open PDF
            doc = fitz.open(file_path)
            total_pages = doc.page_count

            elements = []
            text_content_parts = []

            # Process each page
            for page_num in range(total_pages):
                page = doc[page_num]

                # Extract text with basic method
                if not self.enable_ocr:
                    page_elements = self._extract_text_basic(page, page_num)
                else:
                    # Use OCR for scanned documents
                    page_elements = self._extract_text_with_ocr(page, page_num, doc)

                elements.extend(page_elements)

                # Add layout recognition if enabled
                if self.enable_layout:
                    layout_elements = self._recognize_page_layout(page, page_num, doc)
                    elements.extend(layout_elements)

                # Add table structure recognition if enabled
                if self.enable_table_structure:
                    table_elements = self._recognize_page_tables(page, page_num, doc)
                    elements.extend(table_elements)

            # Combine all text
            text_content = "\n\n".join([e.content for e in elements if e.content])

            doc.close()

            processing_time = time.time() - start_time

            return ParsedDocument(
                filename=self._get_filename(file_path),
                file_path=file_path,
                total_pages=total_pages,
                elements=elements,
                text_content=text_content,
                parsing_level=self.parsing_level,
                processing_time=processing_time,
                metadata={
                    "parser": "PDFParser",
                    "ocr_enabled": self.enable_ocr,
                    "layout_enabled": self.enable_layout,
                    "table_structure_enabled": self.enable_table_structure
                }
            )

        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {e}")
            raise

    def supported_formats(self) -> List[str]:
        """Supported file formats"""
        return [".pdf"]

    def _extract_text_basic(self, page: Any, page_num: int) -> List[ParsedElement]:
        """Extract text using PyMuPDF basic text extraction"""
        elements = []

        # Get text blocks
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block.get("type") == 0:  # Text block
                # Combine lines in block
                lines = block.get("lines", [])
                text = " ".join([
                    "".join([span.get("text", "") for span in line.get("spans", [])])
                    for line in lines
                ])

                if text.strip():
                    bbox = block.get("bbox")
                    elements.append(
                        ParsedElement(
                            type="text",
                            content=text,
                            page=page_num,
                            bbox=bbox,
                            metadata={"source": "basic_extraction"}
                        )
                    )

        return elements

    def _extract_text_with_ocr(
        self,
        page: Any,
        page_num: int,
        doc: Any
    ) -> List[ParsedElement]:
        """Extract text using OCR"""
        elements = []

        try:
            # Initialize OCR if needed
            if self._ocr_selector is None:
                from ..ocr_selector import OCREngineSelector
                self._ocr_selector = OCREngineSelector()

            # Convert page to image
            pix = page.get_pixmap(dpi=150)

            # Save to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                pix.save(tmp_path)

            try:
                # Run OCR
                ocr_result = self._ocr_selector.recognize_image(tmp_path)

                # Convert OCR results to elements
                for text_block in ocr_result.text_blocks:
                    elements.append(
                        ParsedElement(
                            type="text",
                            content=text_block.text,
                            page=page_num,
                            bbox=text_block.bbox,
                            metadata={
                                "source": "ocr",
                                "confidence": text_block.confidence
                            }
                        )
                    )
            finally:
                # Clean up
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.warning(f"OCR failed for page {page_num}: {e}, falling back to basic extraction")
            return self._extract_text_basic(page, page_num)

        return elements

    def _recognize_page_layout(
        self,
        page: Any,
        page_num: int,
        doc: Any
    ) -> List[ParsedElement]:
        """Recognize page layout"""
        elements = []

        try:
            # Initialize layout recognizer if needed
            if self._layout_recognizer is None:
                from ..vision.layout import LayoutRecognizer
                self._layout_recognizer = LayoutRecognizer()

            # Convert page to image
            pix = page.get_pixmap(dpi=150)

            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                pix.save(tmp_path)

            try:
                # Run layout recognition
                layout_result = self._layout_recognizer.recognize_layout(tmp_path)

                # Convert layout elements to parsed elements
                for elem in layout_result.elements:
                    # Skip plain text elements (already extracted)
                    if elem.type.value in ["text"]:
                        continue

                    elements.append(
                        ParsedElement(
                            type=elem.type.value,
                            content=elem.content or "",
                            page=page_num,
                            bbox=elem.bbox,
                            metadata={
                                "confidence": elem.confidence,
                                "source": "layout_recognition"
                            }
                        )
                    )
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.warning(f"Layout recognition failed for page {page_num}: {e}")

        return elements

    def _recognize_page_tables(
        self,
        page: Any,
        page_num: int,
        doc: Any
    ) -> List[ParsedElement]:
        """Recognize table structures"""
        elements = []

        try:
            # Initialize table recognizer if needed
            if self._table_recognizer is None:
                from ..vision.tsr import TableStructureRecognizer
                self._table_recognizer = TableStructureRecognizer()

            # First, detect table regions using layout
            # For now, we'll look for layout elements of type "table"
            table_regions = []

            # Convert page to image
            pix = page.get_pixmap(dpi=150)

            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                pix.save(tmp_path)

            try:
                # Recognize table structures
                tables = self._table_recognizer.recognize_tables_in_page(tmp_path, table_regions)

                for table in tables:
                    # Convert table to natural language
                    table_text = table.to_natural_language()

                    # Also include markdown version
                    table_markdown = table.to_markdown()

                    elements.append(
                        ParsedElement(
                            type="table",
                            content=table_text,
                            page=page_num,
                            bbox=table.bbox,
                            metadata={
                                "source": "table_structure_recognition",
                                "confidence": table.confidence,
                                "num_rows": table.num_rows,
                                "num_cols": table.num_cols,
                                "markdown": table_markdown,
                                "html": table.to_html()
                            }
                        )
                    )
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.warning(f"Table structure recognition failed for page {page_num}: {e}")

        return elements
