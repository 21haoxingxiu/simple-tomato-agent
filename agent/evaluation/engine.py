"""评测执行引擎。"""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from agents.chat_agent import run_chat
from evaluation.metrics import answer_relevance, faithfulness, semantic_similarity
from rag.pipeline import format_context, RetrievedChunk

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    actual_answer: str
    similarity: Optional[float]
    faithfulness: Optional[float]
    relevance: Optional[float]
    score: Optional[float]
    passed: bool
    latency_ms: int
    citations: list[dict]
    error_msg: str = ""


PASS_THRESHOLD = 0.7


def _aggregate(sim: Optional[float], faith: Optional[float], rel: Optional[float]) -> Optional[float]:
    parts: list[tuple[float, float]] = []  # (value, weight)
    if sim is not None:
        parts.append((sim, 0.4))
    if faith is not None:
        parts.append((faith, 0.35))
    if rel is not None:
        parts.append((rel, 0.25))
    if not parts:
        return None
    total_w = sum(w for _, w in parts) or 1.0
    return round(sum(v * w for v, w in parts) / total_w, 4)


async def evaluate_case(
    session: AsyncSession,
    workspace_id: str,
    question: str,
    expected: str,
    kb_id: Optional[str],
) -> EvalResult:
    started = time.time()
    citations: list[RetrievedChunk] = []
    try:
        actual, citations = await run_chat(
            messages=[{"role": "user", "content": question}],
            workspace_id=workspace_id,
            kb_id=kb_id,
            db=session,
        )
    except Exception as exc:
        logger.exception("evaluate_case run_chat failed")
        return EvalResult(
            actual_answer="",
            similarity=None,
            faithfulness=None,
            relevance=None,
            score=None,
            passed=False,
            latency_ms=int((time.time() - started) * 1000),
            citations=[],
            error_msg=str(exc),
        )

    sim = await semantic_similarity(expected, actual) if expected else None
    faith = await faithfulness(question, actual, format_context(citations))
    rel = await answer_relevance(question, actual)
    score = _aggregate(sim, faith, rel)
    passed = score is not None and score >= PASS_THRESHOLD

    return EvalResult(
        actual_answer=actual,
        similarity=round(sim, 4) if sim is not None else None,
        faithfulness=round(faith, 4) if faith is not None else None,
        relevance=round(rel, 4) if rel is not None else None,
        score=score,
        passed=passed,
        latency_ms=int((time.time() - started) * 1000),
        citations=[c.to_dict() for c in citations],
    )
