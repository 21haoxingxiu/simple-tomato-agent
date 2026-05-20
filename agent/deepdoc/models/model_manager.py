"""
Model Manager

Handles downloading, caching, and loading of ML models.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages ML models for DeepDoc

    Handles:
    - Model downloading from HuggingFace
    - Local caching
    - Model versioning
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        hf_mirror: Optional[str] = None
    ):
        """
        Initialize model manager

        Args:
            cache_dir: Directory to cache models (default: ~/.cache/deepdoc)
            hf_mirror: HuggingFace mirror URL (for users in China)
        """
        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.cache/deepdoc"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.hf_mirror = hf_mirror or os.getenv("HF_ENDPOINT")

        # Model registry
        self.models = {
            "layout": {
                "name": "microsoft/layoutlm-base-uncased",
                "type": "layout",
                "size": "~500MB"
            },
            "table-transformer": {
                "name": "microsoft/table-transformer-detection",
                "type": "tsr",
                "size": "~300MB"
            }
        }

    def get_model_path(self, model_name: str) -> Path:
        """
        Get local path for a model

        Args:
            model_name: Name or path of the model

        Returns:
            Path to the cached model
        """
        # Create safe directory name from model name
        safe_name = model_name.replace("/", "_").replace("\\", "_")
        model_path = self.cache_dir / safe_name

        return model_path

    def is_model_cached(self, model_name: str) -> bool:
        """
        Check if model is already cached

        Args:
            model_name: Name of the model

        Returns:
            True if model is cached locally
        """
        model_path = self.get_model_path(model_name)
        return model_path.exists() and any(model_path.iterdir())

    def download_model(
        self,
        model_name: str,
        force: bool = False,
        progress_callback: Optional[callable] = None
    ) -> Path:
        """
        Download a model from HuggingFace

        Args:
            model_name: Name of the model on HuggingFace
            force: Force re-download even if cached
            progress_callback: Optional callback for progress updates

        Returns:
            Path to the downloaded model
        """
        model_path = self.get_model_path(model_name)

        if not force and self.is_model_cached(model_name):
            logger.info(f"Model {model_name} already cached at {model_path}")
            return model_path

        logger.info(f"Downloading model {model_name}...")

        try:
            # Set mirror if provided
            if self.hf_mirror:
                os.environ["HF_ENDPOINT"] = self.hf_mirror

            from huggingface_hub import snapshot_download

            # Download model
            snapshot_download(
                repo_id=model_name,
                local_dir=str(model_path),
                local_dir_use_symlinks=False
            )

            logger.info(f"Model {model_name} downloaded to {model_path}")
            return model_path

        except Exception as e:
            logger.error(f"Failed to download model {model_name}: {e}")
            raise

    def clear_cache(self, model_name: Optional[str] = None):
        """
        Clear model cache

        Args:
            model_name: Specific model to clear (None for all)
        """
        import shutil

        if model_name:
            model_path = self.get_model_path(model_name)
            if model_path.exists():
                shutil.rmtree(model_path)
                logger.info(f"Cleared cache for {model_name}")
        else:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Cleared all model cache")

    def list_cached_models(self) -> Dict[str, Dict[str, Any]]:
        """
        List all cached models

        Returns:
            Dict of model name -> info
        """
        cached = {}

        for model_key, model_info in self.models.items():
            model_name = model_info["name"]
            model_path = self.get_model_path(model_name)

            if self.is_model_cached(model_name):
                # Get cache size
                size = sum(
                    f.stat().st_size
                    for f in model_path.rglob("*")
                    if f.is_file()
                )

                cached[model_key] = {
                    **model_info,
                    "cached": True,
                    "path": str(model_path),
                    "size_mb": size / (1024 * 1024)
                }

        return cached

    def get_cache_size(self) -> float:
        """
        Get total cache size in MB

        Returns:
            Cache size in megabytes
        """
        if not self.cache_dir.exists():
            return 0.0

        size = sum(
            f.stat().st_size
            for f in self.cache_dir.rglob("*")
            if f.is_file()
        )

        return size / (1024 * 1024)
