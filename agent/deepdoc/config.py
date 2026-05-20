"""
DeepDoc Configuration

Manages configuration for DeepDoc features.
"""

import os
from typing import Optional
from pydantic import BaseSettings


class DeepDocConfig(BaseSettings):
    """DeepDoc configuration from environment variables"""

    # Feature flags
    enable_deepdoc: bool = False
    enable_ocr: bool = False
    enable_layout_recognition: bool = False
    enable_table_structure_recognition: bool = False

    # OCR settings
    ocr_engine: str = "auto"  # paddleocr | tesseract | auto
    parsing_level: str = "standard"  # basic | standard | enhanced

    # Cache settings
    deepdoc_cache_dir: Optional[str] = None

    # Model settings
    hf_endpoint: Optional[str] = None

    class Config:
        env_prefix = ""  # No prefix, use variable names directly
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Override with environment variables if set
        self.enable_deepdoc = os.getenv("ENABLE_DEEPDOC", "false").lower() == "true"
        self.enable_ocr = os.getenv("ENABLE_OCR", "false").lower() == "true"
        self.enable_layout_recognition = os.getenv("ENABLE_LAYOUT_RECOGNITION", "false").lower() == "true"
        self.enable_table_structure_recognition = os.getenv("ENABLE_TABLE_STRUCTURE_RECOGNITION", "false").lower() == "true"
        self.ocr_engine = os.getenv("OCR_ENGINE", "auto")
        self.parsing_level = os.getenv("DOCUMENT_PARSING_LEVEL", "standard")
        self.deepdoc_cache_dir = os.getenv("DEEPDOC_CACHE_DIR")
        self.hf_endpoint = os.getenv("HF_ENDPOINT")

        # If parsing level is enhanced, enable all features
        if self.parsing_level == "enhanced":
            self.enable_ocr = True
            self.enable_layout_recognition = True
            self.enable_table_structure_recognition = True

    def is_deepdoc_enabled(self) -> bool:
        """Check if any DeepDoc feature is enabled"""
        return (
            self.enable_deepdoc or
            self.enable_ocr or
            self.enable_layout_recognition or
            self.enable_table_structure_recognition
        )


# Global configuration instance
_config: Optional[DeepDocConfig] = None


def get_deepdoc_config() -> DeepDocConfig:
    """Get DeepDoc configuration instance"""
    global _config
    if _config is None:
        _config = DeepDocConfig()
    return _config


def reload_config():
    """Reload configuration from environment"""
    global _config
    _config = DeepDocConfig()
