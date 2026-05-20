"""
Vision Module - Document Layout and Structure Recognition

Provides:
- Layout recognition (titles, text, tables, figures, etc.)
- Table structure recognition (TSR)
- Visual element detection
"""

from .layout import LayoutRecognizer
from .tsr import TableStructureRecognizer

__all__ = [
    "LayoutRecognizer",
    "TableStructureRecognizer",
]
