"""
OCR Base Class and Interface

Defines the standard interface for OCR engines.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class OCRResult(BaseModel):
    """OCR recognition result for a single text block"""

    text: str = Field(..., description="Recognized text content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Recognition confidence score")
    bbox: Optional[Tuple[float, float, float, float]] = Field(
        None, description="Bounding box coordinates (x0, y0, x1, y1)"
    )
    page: Optional[int] = Field(None, description="Page number (for multi-page documents)")


class OCRPageResult(BaseModel):
    """OCR result for a single page"""

    page_number: int = Field(..., description="Page number (0-indexed)")
    width: float = Field(..., description="Page width")
    height: float = Field(..., description="Page height")
    text_blocks: List[OCRResult] = Field(default_factory=list, description="Text blocks on this page")
    average_confidence: float = Field(0.0, description="Average confidence score for this page")

    def get_full_text(self) -> str:
        """Get all text from this page concatenated"""
        return "\n".join([block.text for block in self.text_blocks])


class OCRDocumentResult(BaseModel):
    """OCR result for an entire document"""

    pages: List[OCRPageResult] = Field(default_factory=list, description="OCR results for each page")
    total_pages: int = Field(0, description="Total number of pages processed")
    total_text_blocks: int = Field(0, description="Total number of text blocks recognized")
    processing_time: float = Field(0.0, description="Total processing time in seconds")
    engine: str = Field(..., description="OCR engine used")

    def get_full_text(self) -> str:
        """Get all text from the document concatenated"""
        return "\n\n".join([page.get_full_text() for page in self.pages])


class BaseOCR(ABC):
    """Abstract base class for OCR engines"""

    def __init__(self, language: str = "ch", **kwargs):
        """
        Initialize OCR engine

        Args:
            language: Language code (e.g., 'ch' for Chinese, 'en' for English)
            **kwargs: Additional engine-specific parameters
        """
        self.language = language
        self.config = kwargs

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    def is_available(self) -> bool:
        """
        Check if the OCR engine is available

        Returns:
            True if the engine is properly installed and ready
        """
        return True

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages

        Returns:
            List of language codes
        """
        return ["ch", "en"]

    def preprocess_image(self, image_path: str, **kwargs) -> Any:
        """
        Preprocess image before OCR (optional)

        Args:
            image_path: Path to the image
            **kwargs: Additional parameters

        Returns:
            Preprocessed image data
        """
        return image_path

    def postprocess_result(self, result: OCRPageResult, **kwargs) -> OCRPageResult:
        """
        Postprocess OCR result (optional)

        Args:
            result: Initial OCR result
            **kwargs: Additional parameters

        Returns:
            Postprocessed OCR result
        """
        return result

    def _calculate_average_confidence(self, text_blocks: List[OCRResult]) -> float:
        """Calculate average confidence score"""
        if not text_blocks:
            return 0.0
        return sum(block.confidence for block in text_blocks) / len(text_blocks)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(language={self.language})"
