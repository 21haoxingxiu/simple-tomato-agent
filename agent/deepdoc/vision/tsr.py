"""
Table Structure Recognition (TSR) Module

Detects table structures and converts them to natural language.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
import html

logger = logging.getLogger(__name__)


class TableCell(BaseModel):
    """A single table cell"""

    text: str = Field(..., description="Cell text content")
    row: int = Field(..., description="Row index (0-indexed)")
    col: int = Field(..., description="Column index (0-indexed)")
    row_span: int = Field(1, description="Number of rows this cell spans")
    col_span: int = Field(1, description="Number of columns this cell spans")
    is_header: bool = Field(False, description="Whether this is a header cell")


class TableStructure(BaseModel):
    """Detected table structure"""

    cells: List[TableCell] = Field(default_factory=list, description="Table cells")
    num_rows: int = Field(0, description="Total number of rows")
    num_cols: int = Field(0, description="Total number of columns")
    bbox: Optional[Tuple[float, float, float, float]] = Field(
        None, description="Bounding box in document"
    )
    page: int = Field(0, description="Page number")
    confidence: float = Field(0.0, description="Detection confidence")

    def to_markdown(self) -> str:
        """Convert table to Markdown format"""
        if not self.cells:
            return ""

        # Create grid
        grid = [[None for _ in range(self.num_cols)] for _ in range(self.num_rows)]

        # Fill grid
        for cell in self.cells:
            grid[cell.row][cell.col] = cell

        # Build markdown
        lines = []

        for row_idx in range(self.num_rows):
            cells = []
            for col_idx in range(self.num_cols):
                cell = grid[row_idx][col_idx]
                if cell:
                    cells.append(cell.text)
                else:
                    cells.append("")

            lines.append("| " + " | ".join(cells) + " |")

            # Add header separator after first row
            if row_idx == 0:
                lines.append("| " + " | ".join(["---"] * self.num_cols) + " |")

        return "\n".join(lines)

    def to_html(self) -> str:
        """Convert table to HTML format"""
        if not self.cells:
            return ""

        # Create grid
        grid = [[None for _ in range(self.num_cols)] for _ in range(self.num_rows)]

        # Fill grid
        for cell in self.cells:
            grid[cell.row][cell.col] = cell

        # Build HTML
        html_lines = ["<table>"]

        for row_idx in range(self.num_rows):
            html_lines.append("  <tr>")
            for col_idx in range(self.num_cols):
                cell = grid[row_idx][col_idx]
                if cell:
                    tag = "th" if cell.is_header else "td"
                    attrs = []
                    if cell.row_span > 1:
                        attrs.append(f'rowspan="{cell.row_span}"')
                    if cell.col_span > 1:
                        attrs.append(f'colspan="{cell.col_span}"')

                    attr_str = " " + " ".join(attrs) if attrs else ""
                    html_lines.append(
                        f'    <{tag}{attr_str}>{html.escape(cell.text)}</{tag}>'
                    )
            html_lines.append("  </tr>")

        html_lines.append("</table>")
        return "\n".join(html_lines)

    def to_natural_language(self) -> str:
        """Convert table to natural language description"""
        if not self.cells:
            return ""

        # Group cells by row
        rows = {}
        for cell in self.cells:
            if cell.row not in rows:
                rows[cell.row] = []
            rows[cell.row].append(cell)

        # Sort rows
        sorted_rows = [rows[i] for i in sorted(rows.keys())]

        # Extract header if first row
        header_cells = []
        if sorted_rows and all(c.is_header for c in sorted_rows[0]):
            header_cells = sorted_rows[0]
            sorted_rows = sorted_rows[1:]

        # Build description
        descriptions = []

        if header_cells:
            headers = [c.text for c in header_cells]
            descriptions.append(f"表头包含：{', '.join(headers)}。")

        for row_idx, row_cells in enumerate(sorted_rows, 1):
            if header_cells:
                # Match cells to headers
                row_desc = []
                for cell in sorted(row_cells, key=lambda c: c.col):
                    if cell.col < len(header_cells):
                        header = header_cells[cell.col].text
                        row_desc.append(f"{header}为{cell.text}")
                    else:
                        row_desc.append(cell.text)

                descriptions.append(f"第{row_idx}行数据：" + "，".join(row_desc) + "。")
            else:
                # No headers, just list values
                values = [c.text for c in sorted(row_cells, key=lambda c: c.col)]
                descriptions.append(f"第{row_idx}行：" + "，".join(values) + "。")

        return " ".join(descriptions)


class TableStructureRecognizer:
    """
    Table structure recognition using pre-trained models

    Detects table cells, rows, columns, and headers.
    """

    def __init__(
        self,
        model_name: str = "microsoft/table-transformer-detection",
        device: str = "cpu",
        **kwargs
    ):
        """
        Initialize table structure recognizer

        Args:
            model_name: HuggingFace model name for TSR
            device: Device to run model on ('cpu' or 'cuda')
            **kwargs: Additional model parameters
        """
        self.model_name = model_name
        self.device = device
        self.config = kwargs
        self._model = None
        self._processor = None

    def _init_model(self):
        """Lazy initialization of TSR model"""
        if self._model is None:
            try:
                from transformers import AutoModelForObjectDetection, AutoImageProcessor

                logger.info(f"Loading TSR model: {self.model_name}")

                self._processor = AutoImageProcessor.from_pretrained(self.model_name)
                self._model = AutoModelForObjectDetection.from_pretrained(self.model_name)
                self._model.to(self.device)
                self._model.eval()

                logger.info("TSR model loaded successfully")

            except ImportError:
                logger.warning(
                    "Transformers not installed. Using basic table detection. "
                    "Install with: pip install transformers torch"
                )
            except Exception as e:
                logger.error(f"Failed to load TSR model: {e}")

    def recognize_table(
        self,
        image_path: str,
        table_bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> TableStructure:
        """
        Recognize table structure in an image

        Args:
            image_path: Path to the image
            table_bbox: Optional bounding box to crop table region

        Returns:
            TableStructure with detected cells and structure
        """
        try:
            from PIL import Image

            # Open image
            img = Image.open(image_path)

            # Crop to table region if specified
            if table_bbox:
                img = img.crop(table_bbox)

            width, height = img.size

            # Initialize model if needed
            self._init_model()

            # If model loaded, use it
            if self._model and self._processor:
                cells = self._detect_structure_with_model(image_path, img)
            else:
                # Fallback to basic detection
                cells = self._basic_table_detection(img)

            # Calculate table dimensions
            if cells:
                num_rows = max(c.row for c in cells) + 1
                num_cols = max(c.col for c in cells) + 1
            else:
                num_rows = 0
                num_cols = 0

            return TableStructure(
                cells=cells,
                num_rows=num_rows,
                num_cols=num_cols,
                bbox=table_bbox,
                confidence=0.8 if (self._model and self._processor) else 0.5
            )

        except Exception as e:
            logger.error(f"Table structure recognition failed for {image_path}: {e}")
            raise

    def recognize_tables_in_page(
        self,
        image_path: str,
        table_regions: Optional[List[Tuple[float, float, float, float]]] = None
    ) -> List[TableStructure]:
        """
        Recognize multiple tables in a page

        Args:
            image_path: Path to the page image
            table_regions: Optional list of table bounding boxes

        Returns:
            List of TableStructure for each detected table
        """
        if table_regions:
            # Process each table region
            tables = []
            for bbox in table_regions:
                table = self.recognize_table(image_path, bbox)
                tables.append(table)
            return tables
        else:
            # Detect tables automatically
            # TODO: Implement automatic table detection
            return []

    def _detect_structure_with_model(
        self,
        image_path: str,
        image: Any
    ) -> List[TableCell]:
        """Use ML model for table structure detection"""
        import torch

        # Process image
        encoding = self._processor(images=image, return_tensors="pt")
        encoding = {k: v.to(self.device) for k, v in encoding.items()}

        # Run inference
        with torch.no_grad():
            outputs = self._model(**encoding)

        # Parse results
        # This is simplified - actual implementation would parse cell predictions
        cells = []

        # TODO: Implement proper cell detection from model outputs
        # For now, return empty list

        return cells

    def _basic_table_detection(self, image: Any) -> List[TableCell]:
        """
        Basic table detection without ML models

        Uses heuristics for simple table structures.
        """
        # This is a simplified placeholder
        # In production, you would use image processing techniques
        # to detect grid lines and cells

        return []

    def auto_rotate_table(
        self,
        image_path: str
    ) -> Tuple[Any, int]:
        """
        Automatically detect and correct table rotation

        Args:
            image_path: Path to the table image

        Returns:
            Tuple of (rotated_image, rotation_angle)
        """
        try:
            from PIL import Image

            img = Image.open(image_path)

            # Test OCR confidence at different rotations
            best_angle = 0
            best_confidence = 0.0

            from ..ocr_selector import OCREngineSelector
            ocr = OCREngineSelector()

            for angle in [0, 90, 180, 270]:
                # Rotate image
                rotated = img.rotate(angle, expand=True)

                # Save to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp_path = tmp.name
                    rotated.save(tmp_path)

                try:
                    # Get OCR confidence
                    result = ocr.recognize_image(tmp_path)
                    confidence = result.average_confidence

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_angle = angle
                finally:
                    import os
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

            # Apply best rotation
            if best_angle != 0:
                img = img.rotate(best_angle, expand=True)

            return img, best_angle

        except Exception as e:
            logger.warning(f"Auto-rotation failed: {e}")
            return Image.open(image_path), 0

    def is_available(self) -> bool:
        """Check if table structure recognition is available"""
        try:
            import transformers
            import torch
            return True
        except ImportError:
            return False
