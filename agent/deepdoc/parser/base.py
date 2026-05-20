"""
Base Parser and Parsed Document Models

Defines the interface for document parsers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ParsingLevel(str, Enum):
    """Document parsing intensity levels"""
    BASIC = "basic"  # Text extraction only
    STANDARD = "standard"  # Text + Layout recognition
    FULL = "full"  # OCR + Layout + Table structure recognition


class ParsedElement(BaseModel):
    """A parsed element from a document"""

    type: str = Field(..., description="Element type (text, table, figure, etc.)")
    content: str = Field(..., description="Element content")
    page: int = Field(0, description="Page number (0-indexed)")
    bbox: Optional[tuple] = Field(None, description="Bounding box (x0, y0, x1, y1)")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ParsedDocument(BaseModel):
    """Result of parsing a document"""

    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Path to the document file")
    total_pages: int = Field(0, description="Total number of pages")
    elements: List[ParsedElement] = Field(
        default_factory=list, description="Parsed elements"
    )
    text_content: str = Field("", description="Full text content")
    parsing_level: ParsingLevel = Field(
        ParsingLevel.STANDARD, description="Parsing level used"
    )
    processing_time: float = Field(0.0, description="Processing time in seconds")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )

    def get_elements_by_type(self, element_type: str) -> List[ParsedElement]:
        """Get all elements of a specific type"""
        return [e for e in self.elements if e.type == element_type]

    def get_text_elements(self) -> List[ParsedElement]:
        """Get all text elements"""
        return self.get_elements_by_type("text")

    def get_table_elements(self) -> List[ParsedElement]:
        """Get all table elements"""
        return self.get_elements_by_type("table")

    def get_figure_elements(self) -> List[ParsedElement]:
        """Get all figure elements"""
        return self.get_elements_by_type("figure")


class BaseParser(ABC):
    """Abstract base class for document parsers"""

    def __init__(
        self,
        parsing_level: ParsingLevel = ParsingLevel.STANDARD,
        enable_ocr: bool = False,
        enable_layout: bool = False,
        enable_table_structure: bool = False,
        **kwargs
    ):
        """
        Initialize document parser

        Args:
            parsing_level: Parsing intensity level
            enable_ocr: Whether to enable OCR
            enable_layout: Whether to enable layout recognition
            enable_table_structure: Whether to enable table structure recognition
            **kwargs: Additional parser parameters
        """
        self.parsing_level = parsing_level
        self.enable_ocr = enable_ocr
        self.enable_layout = enable_layout
        self.enable_table_structure = enable_table_structure
        self.config = kwargs

        # Adjust flags based on parsing level
        if parsing_level == ParsingLevel.FULL:
            self.enable_ocr = True
            self.enable_layout = True
            self.enable_table_structure = True
        elif parsing_level == ParsingLevel.STANDARD:
            self.enable_layout = True

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """
        Parse a document file

        Args:
            file_path: Path to the document file

        Returns:
            ParsedDocument with parsed elements and metadata
        """
        pass

    @abstractmethod
    def supported_formats(self) -> List[str]:
        """
        Get list of supported file formats

        Returns:
            List of file extensions (e.g., ['.pdf', '.docx'])
        """
        pass

    def can_parse(self, file_path: str) -> bool:
        """
        Check if this parser can handle the given file

        Args:
            file_path: Path to the file

        Returns:
            True if the file format is supported
        """
        import os
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_formats()

    def _get_filename(self, file_path: str) -> str:
        """Extract filename from path"""
        import os
        return os.path.basename(file_path)
