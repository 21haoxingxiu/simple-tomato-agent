"""
Parsing Cache Manager

Caches parsing results to avoid re-processing documents.
"""

import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ParsingCache:
    """
    Manages parsing result cache

    Caches:
    - OCR results
    - Layout recognition results
    - Table structure results
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        ttl_days: int = 30
    ):
        """
        Initialize parsing cache

        Args:
            cache_dir: Directory to store cache (default: ./cache/deepdoc)
            ttl_days: Time-to-live in days (default: 30)
        """
        self.cache_dir = Path(cache_dir or "./cache/deepdoc")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_days = ttl_days

    def _get_file_hash(self, file_path: str) -> str:
        """
        Calculate MD5 hash of a file

        Args:
            file_path: Path to the file

        Returns:
            MD5 hash string
        """
        hash_md5 = hashlib.md5()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def _get_cache_key(
        self,
        file_path: str,
        parsing_level: str,
        options: Optional[Dict] = None
    ) -> str:
        """
        Generate cache key for a file

        Args:
            file_path: Path to the file
            parsing_level: Parsing level used
            options: Additional parsing options

        Returns:
            Cache key string
        """
        file_hash = self._get_file_hash(file_path)

        # Include options in key
        options_str = json.dumps(options or {}, sort_keys=True)
        options_hash = hashlib.md5(options_str.encode()).hexdigest()[:8]

        return f"{file_hash}_{parsing_level}_{options_hash}"

    def get_cache_path(self, cache_key: str) -> Path:
        """
        Get cache file path for a key

        Args:
            cache_key: Cache key

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def get(
        self,
        file_path: str,
        parsing_level: str,
        options: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached parsing result

        Args:
            file_path: Path to the file
            parsing_level: Parsing level used
            options: Additional parsing options

        Returns:
            Cached result or None
        """
        cache_key = self._get_cache_key(file_path, parsing_level, options)
        cache_path = self.get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            # Check TTL
            cached_time = datetime.fromisoformat(cached.get("timestamp", ""))
            if datetime.now() - cached_time > timedelta(days=self.ttl_days):
                logger.info(f"Cache expired for {file_path}")
                cache_path.unlink()
                return None

            logger.info(f"Cache hit for {file_path}")
            return cached.get("result")

        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
            return None

    def set(
        self,
        file_path: str,
        parsing_level: str,
        result: Dict[str, Any],
        options: Optional[Dict] = None
    ):
        """
        Save parsing result to cache

        Args:
            file_path: Path to the file
            parsing_level: Parsing level used
            result: Parsing result to cache
            options: Additional parsing options
        """
        cache_key = self._get_cache_key(file_path, parsing_level, options)
        cache_path = self.get_cache_path(cache_key)

        try:
            cache_data = {
                "file_path": file_path,
                "parsing_level": parsing_level,
                "options": options,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Cached result for {file_path}")

        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")

    def invalidate(self, file_path: str):
        """
        Invalidate cache for a file

        Args:
            file_path: Path to the file
        """
        file_hash = self._get_file_hash(file_path)

        # Find and delete all cache entries for this file
        for cache_file in self.cache_dir.glob(f"{file_hash}_*.json"):
            cache_file.unlink()
            logger.info(f"Invalidated cache: {cache_file.name}")

    def clear(self):
        """Clear all cache"""
        import shutil

        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Cleared all parsing cache")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict with cache stats
        """
        cache_files = list(self.cache_dir.glob("*.json"))

        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "total_entries": len(cache_files),
            "total_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
            "ttl_days": self.ttl_days
        }
