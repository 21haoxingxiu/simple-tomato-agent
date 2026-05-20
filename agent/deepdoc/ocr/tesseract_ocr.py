"""
Tesseract OCR Engine Implementation

Lightweight OCR engine, best for English text.
"""

import time
from typing import List, Optional
import logging

from .base import BaseOCR, OCRResult, OCRPageResult, OCRDocumentResult

logger = logging.getLogger(__name__)


class TesseractOCREngine(BaseOCR):
    """Tesseract OCR engine for text recognition"""

    def __init__(self, language: str = "eng", **kwargs):
        """
        Initialize Tesseract OCR engine

        Args:
            language: Language code (e.g., 'eng', 'chi_sim', 'chi_tra', 'fra', 'deu')
            **kwargs: Additional Tesseract parameters
        """
        super().__init__(language, **kwargs)

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
            import pytesseract
            from PIL import Image

            # Open image
            img = Image.open(image_path)
            width, height = img.size

            # Run OCR with detailed data
            data = pytesseract.image_to_data(
                img,
                lang=self.language,
                output_type=pytesseract.Output.DICT,
                **self.config
            )

            # Parse results
            text_blocks = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text:  # Only include non-empty text
                    confidence = float(data['conf'][i]) / 100.0  # Convert to 0-1 scale
                    bbox = (
                        float(data['left'][i]),
                        float(data['top'][i]),
                        float(data['left'][i] + data['width'][i]),
                        float(data['top'][i] + data['height'][i])
                    )

                    text_blocks.append(
                        OCRResult(
                            text=text,
                            confidence=confidence,
                            bbox=bbox
                        )
                    )

            processing_time = time.time() - start_time
            avg_confidence = self._calculate_average_confidence(text_blocks)

            return OCRPageResult(
                page_number=0,
                width=float(width),
                height=float(height),
                text_blocks=text_blocks,
                average_confidence=avg_confidence
            )

        except ImportError:
            raise ImportError(
                "pytesseract or PIL is not installed. Install with: pip install pytesseract pillow"
            )
        except Exception as e:
            logger.error(f"Tesseract failed to recognize image {image_path}: {e}")
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
                engine="Tesseract"
            )

        except Exception as e:
            logger.error(f"Tesseract failed to recognize PDF {pdf_path}: {e}")
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
        from io import BytesIO
        from PIL import Image

        # Load image from bytes
        img = Image.open(BytesIO(image_bytes))

        import tempfile
        import os

        # Save to temporary file (Tesseract works better with files)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            img.save(tmp_path)

        try:
            return self.recognize_image(tmp_path, **kwargs)
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def is_available(self) -> bool:
        """Check if Tesseract is available"""
        try:
            import pytesseract
            # Try to get tesseract version
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def get_supported_languages(self) -> List[str]:
        """Get list of commonly supported languages"""
        return [
            "eng", "chi_sim", "chi_tra", "fra", "deu", "spa",
            "por", "ita", "rus", "jpn", "kor", "ara"
        ]
