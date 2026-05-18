"""重排:
- 默认 RRF (Reciprocal Rank Fusion) 融合多路结果
- 启用 RERANKER=cross_encoder 时使用 sentence-transformers Cross-Encoder
"""
from __future__ import annotations

import os
import logging
from functools import lru_cache
from typing import Iterable

logger = logging.getLogger(__name__)


def rrf_fuse(
    rankings: Iterable[list[str]], k_const: int = 60, top_k: int = 8
) -> list[tuple[str, float]]:
    """对多个有序 chunk_id 列表做 RRF 融合,返回 [(chunk_id, score)] 倒序。"""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, cid in enumerate(ranking):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k_const + rank + 1)
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return ranked[:top_k]


@lru_cache(maxsize=1)
def _cross_encoder():
    try:
        from sentence_transformers import CrossEncoder

        model = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
        logger.info("Loading CrossEncoder reranker=%s", model)
        return CrossEncoder(model)
    except Exception as exc:
        logger.warning("CrossEncoder load failed: %s — reranker disabled", exc)
        return None


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """candidates: [{chunk_id, content, ...}] 加入 rerank_score 字段后倒序。"""
    model = _cross_encoder()
    if model is None or not candidates:
        return candidates[:top_k]
    pairs = [(query, c["content"]) for c in candidates]
    try:
        scores = model.predict(pairs)
    except Exception as exc:
        logger.warning("CrossEncoder predict failed: %s", exc)
        return candidates[:top_k]
    for c, s in zip(candidates, scores):
        c["rerank_score"] = float(s)
    candidates.sort(key=lambda c: -c.get("rerank_score", 0.0))
    return candidates[:top_k]


def is_cross_encoder_enabled() -> bool:
    return os.getenv("RERANKER", "rrf").lower() in ("cross_encoder", "ce")
