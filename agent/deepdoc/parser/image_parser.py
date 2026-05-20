"""
Image Parser

Parses image files (PNG, JPG, etc.) using OCR.
"""

import time
import logging
from typing import List

from .base import BaseParser, ParsedDocument, ParsedElement, ParsingLevel

logger = logging.getLogger(__name__)


class ImageParser(BaseParser):
    """Parser for image files"""

    def __init__(
        self,
        parsing_level: ParsingLevel = ParsingLevel.FULL,
        **kwargs
    ):
        """
        Initialize image parser

        Args:
            parsing_level: Parsing intensity level
            **kwargs: Additional parameters
        """
        # Image parsing always uses OCR
        super().__init__(parsing_level, enable_ocr=True, **kwargs)

        self._ocr_selector = None

    def parse(self, file_path: str) -> ParsedDocument:
        """
        Parse an image file

        Args:
            file_path: Path to the image file

        Returns:
            ParsedDocument with OCR results
        """
        start_time = time.time()

        try:
            from PIL import Image

            # Open image to get dimensions
            img = Image.open(file_path)
            width, height = img.size
            img.close()

            # Initialize OCR
            if self._ocr_selector is None:
                from ..ocr_selector import OCREngineSelector
                self._ocr_selector = OCREngineSelector()

            # Run OCR
            ocr_result = self._ocr_selector.recognize_image(file_path)

            # Convert to elements
            elements = []
            for text_block in ocr_result.text_blocks:
                elements.append(
                    ParsedElement(
                        type="text",
                        content=text_block.text,
                        page=0,
                        bbox=text_block.bbox,
                        metadata={
                            "source": "ocr",
                            "confidence": text_block.confidence
                        }
                    )
                )

            # Combine text
            text_content = ocr_result.get_full_text()

            processing_time = time.time() - start_time

            return ParsedDocument(
                filename=self._get_filename(file_path),
                file_path=file_path,
                total_pages=1,
                elements=elements,
                text_content=text_content,
                parsing_level=self.parsing_level,
                processing_time=processing_time,
                metadata={
                    "parser": "ImageParser",
                    "image_width": width,
                    "image_height": height,
                    "average_ocr_confidence": ocr_result.average_confidence,
                    "total_text_blocks": len(ocr_result.text_blocks)
                }
            )

        except Exception as e:
            logger.error(f"Failed to parse image {file_path}: {e}")
            raise

    def supported_formats(self) -> List[str]:
        """Supported image formats"""
        return [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"]
