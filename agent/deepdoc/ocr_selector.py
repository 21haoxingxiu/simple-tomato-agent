"""
OCR Engine Selector

Automatically selects the best available OCR engine and handles fallbacks.
"""

import logging
from typing import Optional, Dict, Any

from .ocr.base import BaseOCR, OCRPageResult, OCRDocumentResult
from .ocr.paddle_ocr import PaddleOCREngine
from .ocr.tesseract_ocr import TesseractOCREngine

logger = logging.getLogger(__name__)


class OCREngineSelector:
    """
    Automatically selects and manages OCR engines with fallback support.

    Selection priority:
    1. PaddleOCR (best for Chinese and general use)
    2. Tesseract (fallback for English or when PaddleOCR unavailable)
    """

    ENGINES = {
        "paddleocr": PaddleOCREngine,
        "tesseract": TesseractOCREngine
    }

    def __init__(
        self,
        preferred_engine: Optional[str] = None,
        language: str = "ch",
        fallback: bool = True,
        **kwargs
    ):
        """
        Initialize OCR engine selector

        Args:
            preferred_engine: Preferred OCR engine ('paddleocr' or 'tesseract')
            language: Language code
            fallback: Whether to enable fallback to other engines
            **kwargs: Additional engine parameters
        """
        self.preferred_engine = preferred_engine
        self.language = language
        self.fallback = fallback
        self.config = kwargs
        self._engine = None
        self._engine_name = None

    def _detect_best_engine(self) -> tuple:
        """
        Detect the best available OCR engine

        Returns:
            Tuple of (engine_name, engine_class)
        """
        # If preferred engine is specified and available, use it
        if self.preferred_engine:
            engine_class = self.ENGINES.get(self.preferred_engine.lower())
            if engine_class:
                try:
                    # Test if engine is available
                    engine = engine_class(language=self.language, **self.config)
                    if engine.is_available():
                        logger.info(f"Using preferred OCR engine: {self.preferred_engine}")
                        return self.preferred_engine, engine_class
                except Exception as e:
                    logger.warning(f"Preferred engine {self.preferred_engine} failed: {e}")

        # Auto-select based on availability
        if not self.fallback:
            # No fallback, just try preferred or default
            engine_name = self.preferred_engine or "paddleocr"
            engine_class = self.ENGINES.get(engine_name.lower())
            if engine_class:
                return engine_name, engine_class
            else:
                raise ValueError(f"OCR engine '{engine_name}' not found")

        # Try engines in order of preference
        engine_order = ["paddleocr", "tesseract"]

        for engine_name in engine_order:
            engine_class = self.ENGINES.get(engine_name)
            if engine_class:
                try:
                    # Test if engine is available
                    engine = engine_class(language=self.language, **self.config)
                    if engine.is_available():
                        logger.info(f"Auto-selected OCR engine: {engine_name}")
                        return engine_name, engine_class
                except Exception as e:
                    logger.debug(f"Engine {engine_name} not available: {e}")
                    continue

        raise RuntimeError("No OCR engine available. Please install PaddleOCR or Tesseract.")

    def get_engine(self) -> BaseOCR:
        """
        Get the OCR engine instance (lazy initialization)

        Returns:
            BaseOCR instance
        """
        if self._engine is None:
            engine_name, engine_class = self._detect_best_engine()
            self._engine = engine_class(language=self.language, **self.config)
            self._engine_name = engine_name

        return self._engine

    def recognize_image(
        self,
        image_path: str,
        **kwargs
    ) -> OCRPageResult:
        """
        Recognize text from image with fallback support

        Args:
            image_path: Path to the image
            **kwargs: Additional parameters

        Returns:
            OCRPageResult
        """
        engine = self.get_engine()

        try:
            return engine.recognize_image(image_path, **kwargs)
        except Exception as e:
            logger.error(f"OCR failed with {self._engine_name}: {e}")

            if self.fallback:
                # Try fallback engine
                return self._try_fallback(
                    "recognize_image",
                    image_path=image_path,
                    **kwargs
                )
            else:
                raise

    def recognize_pdf(
        self,
        pdf_path: str,
        pages: Optional[list] = None,
        **kwargs
    ) -> OCRDocumentResult:
        """
        Recognize text from PDF with fallback support

        Args:
            pdf_path: Path to the PDF
            pages: List of page numbers to process
            **kwargs: Additional parameters

        Returns:
            OCRDocumentResult
        """
        engine = self.get_engine()

        try:
            return engine.recognize_pdf(pdf_path, pages=pages, **kwargs)
        except Exception as e:
            logger.error(f"OCR failed with {self._engine_name}: {e}")

            if self.fallback:
                # Try fallback engine
                return self._try_fallback(
                    "recognize_pdf",
                    pdf_path=pdf_path,
                    pages=pages,
                    **kwargs
                )
            else:
                raise

    def _try_fallback(self, method: str, **kwargs) -> Any:
        """
        Try fallback OCR engine

        Args:
            method: Method name to call
            **kwargs: Method parameters

        Returns:
            Result from fallback engine
        """
        # Determine fallback engine
        fallback_name = "tesseract" if self._engine_name == "paddleocr" else "paddleocr"
        fallback_class = self.ENGINES.get(fallback_name)

        if not fallback_class:
            raise RuntimeError("No fallback OCR engine available")

        try:
            logger.info(f"Trying fallback OCR engine: {fallback_name}")
            fallback_engine = fallback_class(language=self.language, **self.config)

            if not fallback_engine.is_available():
                raise RuntimeError(f"Fallback engine {fallback_name} not available")

            method_func = getattr(fallback_engine, method)
            return method_func(**kwargs)

        except Exception as e:
            logger.error(f"Fallback OCR engine {fallback_name} also failed: {e}")
            raise RuntimeError(f"All OCR engines failed. Last error: {e}")

    @classmethod
    def list_available_engines(cls) -> Dict[str, bool]:
        """
        List all available OCR engines

        Returns:
            Dict mapping engine name to availability status
        """
        availability = {}

        for engine_name, engine_class in cls.ENGINES.items():
            try:
                engine = engine_class()
                availability[engine_name] = engine.is_available()
            except Exception:
                availability[engine_name] = False

        return availability


def get_ocr_engine(
    preferred_engine: Optional[str] = None,
    language: str = "ch",
    **kwargs
) -> BaseOCR:
    """
    Convenience function to get an OCR engine

    Args:
        preferred_engine: Preferred OCR engine name
        language: Language code
        **kwargs: Additional engine parameters

    Returns:
        BaseOCR instance
    """
    selector = OCREngineSelector(
        preferred_engine=preferred_engine,
        language=language,
        **kwargs
    )
    return selector.get_engine()
