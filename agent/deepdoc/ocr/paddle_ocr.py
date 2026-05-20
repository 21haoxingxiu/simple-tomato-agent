"""
PaddleOCR Engine Implementation

Best for Chinese text recognition with high accuracy.
"""

import time
from typing import List, Optional, Any
import logging

from .base import BaseOCR, OCRResult, OCRPageResult, OCRDocumentResult

logger = logging.getLogger(__name__)


class PaddleOCREngine(BaseOCR):
    """PaddleOCR engine for text recognition"""

    def __init__(self, language: str = "ch", use_gpu: bool = False, **kwargs):
        """
        Initialize PaddleOCR engine

        Args:
            language: Language code ('ch', 'en', 'french', 'german', 'korean', 'japan', etc.)
            use_gpu: Whether to use GPU for acceleration
            **kwargs: Additional PaddleOCR parameters
        """
        super().__init__(language, **kwargs)
        self.use_gpu = use_gpu
        self._ocr = None

    def _init_ocr(self):
        """Lazy initialization of PaddleOCR"""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR

                self._ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.language,
                    use_gpu=self.use_gpu,
                    show_log=False,
                    **self.config
                )
                logger.info(f"PaddleOCR initialized with language={self.language}, use_gpu={self.use_gpu}")
            except ImportError:
                raise ImportError(
                    "PaddleOCR is not installed. Install it with: pip install paddleocr"
                )
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {e}")
                raise

    def recognize_image(
        self,
        image_path: str,
        detect_language: bool = False,
        **kwargs
    ) -> OCRPageResult:
        """
        Recognize text from an image file

        Args:
            image_path: Path to the image file
            detect_language: Whether to automatically detect language
            **kwargs: Additional parameters

        Returns:
            OCRPageResult with recognized text and metadata
        """
        start_time = time.time()

        try:
            self._init_ocr()

            # Get image dimensions
            width, height = self._get_image_dimensions(image_path)

            # Run OCR
            result = self._ocr.ocr(image_path, cls=True)

            # Parse results
            text_blocks = []
            if result and result[0]:
                for line in result[0]:
                    if line:
                        # PaddleOCR format: [[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, confidence)]
                        bbox_points = line[0]
                        text, confidence = line[1]

                        # Convert bbox points to (x0, y0, x1, y1)
                        x_coords = [p[0] for p in bbox_points]
                        y_coords = [p[1] for p in bbox_points]
                        bbox = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

                        text_blocks.append(
                            OCRResult(
                                text=text,
                                confidence=float(confidence),
                                bbox=bbox
                            )
                        )

            processing_time = time.time() - start_time
            avg_confidence = self._calculate_average_confidence(text_blocks)

            return OCRPageResult(
                page_number=0,
                width=width,
                height=height,
                text_blocks=text_blocks,
                average_confidence=avg_confidence
            )

        except Exception as e:
            logger.error(f"PaddleOCR failed to recognize image {image_path}: {e}")
            raise

    def recognize_pdf(
        self,
        pdf_path: str,
        pages: Optional[List[int]] = None,
        **kwargs
    ) -> OCRDocumentResult:
        """
        Recognize text from a PDF file

        Args:
            pdf_path: Path to the PDF file
            pages: List of page numbers to process (None for all pages)
            **kwargs: Additional parameters

        Returns:
            OCRDocumentResult with recognized text and metadata
        """
        start_time = time.time()

        try:
            import fitz  # PyMuPDF

            self._init_ocr()

            # Open PDF
            doc = fitz.open(pdf_path)
            total_pages = doc.page_count

            # Determine which pages to process
            page_indices = pages if pages else range(total_pages)

            ocr_pages = []
            for page_idx in page_indices:
                # Convert PDF page to image
                page = doc[page_idx]
                pix = page.get_pixmap(dpi=150)

                # Save to temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp_path = tmp.name
                    pix.save(tmp_path)

                # Run OCR on the page image
                try:
                    ocr_result = self.recognize_image(tmp_path, **kwargs)
                    ocr_result.page_number = page_idx
                    ocr_pages.append(ocr_result)
                finally:
                    # Clean up temp file
                    import os
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

            doc.close()

            processing_time = time.time() - start_time

            return OCRDocumentResult(
                pages=ocr_pages,
                total_pages=len(ocr_pages),
                total_text_blocks=sum(len(p.text_blocks) for p in ocr_pages),
                processing_time=processing_time,
                engine="PaddleOCR"
            )

        except Exception as e:
            logger.error(f"PaddleOCR failed to recognize PDF {pdf_path}: {e}")
            raise

    def recognize_image_bytes(
        self,
        image_bytes: bytes,
        **kwargs
    ) -> OCRPageResult:
        """
        Recognize text from image bytes

        Args:
            image_bytes: Raw image bytes
            **kwargs: Additional parameters

        Returns:
            OCRPageResult with recognized text and metadata
        """
        import tempfile
        import os

        # Save bytes to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(image_bytes)

        try:
            return self.recognize_image(tmp_path, **kwargs)
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def is_available(self) -> bool:
        """Check if PaddleOCR is available"""
        try:
            from paddleocr import PaddleOCR
            return True
        except ImportError:
            return False

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return [
            "ch", "en", "french", "german", "korean", "japan",
            "chinese_cht", "ta", "te", "ka", "latin", "arabic",
            "cyrillic", "devanagari"
        ]

    def _get_image_dimensions(self, image_path: str) -> tuple:
        """Get image width and height"""
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                return img.size
        except Exception:
            return (0, 0)
