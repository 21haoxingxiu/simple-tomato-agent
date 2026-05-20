"""
Layout Recognition Module

Detects and classifies document layout elements (titles, text, tables, figures, etc.)
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LayoutElementType(str, Enum):
    """Types of layout elements in documents"""
    TEXT = "text"
    TITLE = "title"
    LIST = "list"
    TABLE = "table"
    FIGURE = "figure"
    FIGURE_CAPTION = "figure_caption"
    TABLE_CAPTION = "table_caption"
    HEADER = "header"
    FOOTER = "footer"
    EQUATION = "equation"
    CODE = "code"
    ABSTRACT = "abstract"
    REFERENCE = "reference"


class LayoutElement(BaseModel):
    """A single layout element in a document"""

    type: LayoutElementType = Field(..., description="Type of layout element")
    bbox: Tuple[float, float, float, float] = Field(
        ..., description="Bounding box (x0, y0, x1, y1)"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    content: Optional[str] = Field(None, description="Text content if available")
    page: int = Field(0, description="Page number (0-indexed)")

    @property
    def width(self) -> float:
        """Get element width"""
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> float:
        """Get element height"""
        return self.bbox[3] - self.bbox[1]


class LayoutPageResult(BaseModel):
    """Layout recognition result for a single page"""

    page_number: int = Field(..., description="Page number (0-indexed)")
    width: float = Field(..., description="Page width")
    height: float = Field(..., description="Page height")
    elements: List[LayoutElement] = Field(
        default_factory=list, description="Layout elements on this page"
    )


class LayoutRecognizer:
    """
    Document layout recognition using pre-trained models

    Uses LayoutLM or similar models for document structure detection.
    """

    def __init__(
        self,
        model_name: str = "microsoft/layoutlm-base-uncased",
        device: str = "cpu",
        **kwargs
    ):
        """
        Initialize layout recognizer

        Args:
            model_name: HuggingFace model name for layout recognition
            device: Device to run model on ('cpu' or 'cuda')
            **kwargs: Additional model parameters
        """
        self.model_name = model_name
        self.device = device
        self.config = kwargs
        self._model = None
        self._processor = None

    def _init_model(self):
        """Lazy initialization of layout recognition model"""
        if self._model is None:
            try:
                from transformers import LayoutLMv3ForTokenClassification, LayoutLMv3Processor

                logger.info(f"Loading layout model: {self.model_name}")

                self._processor = LayoutLMv3Processor.from_pretrained(self.model_name)
                self._model = LayoutLMv3ForTokenClassification.from_pretrained(self.model_name)
                self._model.to(self.device)
                self._model.eval()

                logger.info("Layout model loaded successfully")

            except ImportError:
                logger.warning(
                    "Transformers not installed. Using basic layout detection. "
                    "Install with: pip install transformers torch"
                )
            except Exception as e:
                logger.error(f"Failed to load layout model: {e}")

    def recognize_layout(
        self,
        image_path: str,
        use_ocr: bool = True
    ) -> LayoutPageResult:
        """
        Recognize layout elements in an image

        Args:
            image_path: Path to the image
            use_ocr: Whether to extract text content using OCR

        Returns:
            LayoutPageResult with detected elements
        """
        try:
            from PIL import Image

            # Open image
            img = Image.open(image_path)
            width, height = img.size

            # Initialize model if needed
            self._init_model()

            # If model loaded successfully, use it
            if self._model and self._processor:
                elements = self._detect_with_model(image_path, img)
            else:
                # Fallback to basic detection
                elements = self._basic_layout_detection(image_path, img)

            # Optionally extract text content
            if use_ocr:
                elements = self._extract_text_for_elements(elements, image_path)

            return LayoutPageResult(
                page_number=0,
                width=float(width),
                height=float(height),
                elements=elements
            )

        except Exception as e:
            logger.error(f"Layout recognition failed for {image_path}: {e}")
            raise

    def recognize_pdf_layout(
        self,
        pdf_path: str,
        pages: Optional[List[int]] = None
    ) -> List[LayoutPageResult]:
        """
        Recognize layout in PDF pages

        Args:
            pdf_path: Path to the PDF file
            pages: List of page numbers to process (None for all)

        Returns:
            List of LayoutPageResult for each page
        """
        try:
            import fitz  # PyMuPDF
            import tempfile

            doc = fitz.open(pdf_path)
            page_indices = pages if pages else range(doc.page_count)

            results = []
            for page_idx in page_indices:
                # Convert PDF page to image
                page = doc[page_idx]
                pix = page.get_pixmap(dpi=150)

                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp_path = tmp.name
                    pix.save(tmp_path)

                try:
                    result = self.recognize_layout(tmp_path)
                    result.page_number = page_idx
                    results.append(result)
                finally:
                    import os
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

            doc.close()
            return results

        except Exception as e:
            logger.error(f"PDF layout recognition failed for {pdf_path}: {e}")
            raise

    def _detect_with_model(
        self,
        image_path: str,
        image: Any
    ) -> List[LayoutElement]:
        """Use ML model for layout detection"""
        import torch

        # Process image
        encoding = self._processor(
            image,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )
        encoding = {k: v.to(self.device) for k, v in encoding.items()}

        # Run inference
        with torch.no_grad():
            outputs = self._model(**encoding)

        # Parse results
        predictions = outputs.logits.argmax(-1).squeeze().tolist()

        # Convert predictions to layout elements
        # This is simplified - actual implementation would parse token-level predictions
        elements = []

        # For now, return basic elements
        # TODO: Implement proper token-to-element conversion

        return elements

    def _basic_layout_detection(
        self,
        image_path: str,
        image: Any
    ) -> List[LayoutElement]:
        """
        Basic layout detection without ML models

        Uses heuristics and image processing for simple layouts.
        """
        # This is a simplified implementation
        # In production, you would use proper computer vision techniques

        width, height = image.size

        # Return a single text element covering the whole page
        return [
            LayoutElement(
                type=LayoutElementType.TEXT,
                bbox=(0, 0, float(width), float(height)),
                confidence=0.5,
                page=0
            )
        ]

    def _extract_text_for_elements(
        self,
        elements: List[LayoutElement],
        image_path: str
    ) -> List[LayoutElement]:
        """Extract text content for each element using OCR"""
        try:
            from ..ocr_selector import OCREngineSelector

            ocr = OCREngineSelector()
            ocr_result = ocr.recognize_image(image_path)

            # Match OCR text blocks to layout elements
            for element in elements:
                # Find OCR blocks within this element's bbox
                element_text = []
                for block in ocr_result.text_blocks:
                    if self._bbox_overlap(element.bbox, block.bbox):
                        element_text.append(block.text)

                if element_text:
                    element.content = " ".join(element_text)

            return elements

        except Exception as e:
            logger.warning(f"Failed to extract text for layout elements: {e}")
            return elements

    def _bbox_overlap(
        self,
        bbox1: Tuple[float, float, float, float],
        bbox2: Tuple[float, float, float, float],
        threshold: float = 0.5
    ) -> bool:
        """Check if two bounding boxes overlap"""
        x0_1, y0_1, x1_1, y1_1 = bbox1
        x0_2, y0_2, x1_2, y1_2 = bbox2

        # Calculate intersection
        x0_i = max(x0_1, x0_2)
        y0_i = max(y0_1, y0_2)
        x1_i = min(x1_1, x1_2)
        y1_i = min(y1_1, y1_2)

        if x0_i >= x1_i or y0_i >= y1_i:
            return False

        intersection = (x1_i - x0_i) * (y1_i - y0_i)
        area1 = (x1_1 - x0_1) * (y1_1 - y0_1)
        area2 = (x1_2 - x0_2) * (y1_2 - y0_2)

        iou = intersection / (area1 + area2 - intersection)

        return iou > threshold

    def is_available(self) -> bool:
        """Check if layout recognition is available"""
        try:
            import transformers
            import torch
            return True
        except ImportError:
            return False
