"""
OCR (Optical Character Recognition) Module

Supports multiple OCR engines:
- PaddleOCR: Best for Chinese text recognition
- Tesseract: Lightweight option for English text
"""

from .base import BaseOCR, OCRResult
from .paddle_ocr import PaddleOCREngine
from .tesseract_ocr import TesseractOCREngine

__all__ = [
    "BaseOCR",
    "OCRResult",
    "PaddleOCREngine",
    "TesseractOCREngine",
]
