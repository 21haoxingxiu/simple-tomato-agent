"""评测指标。"""
from __future__ import annotations

from typing import Optional

import json
import logging
import math
import os
import re
from functools import lru_cache

logger = logging.getLogger(__name__)


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


async def semantic_similarity(expected: str, actual: str) -> float:
    if not expected or not actual:
        return 0.0
    from rag.embeddings import get_embeddings

    emb = get_embeddings()
    try:
        vecs = await _aembed(emb, [expected, actual])
        sim = cosine(vecs[0], vecs[1])
        return max(0.0, min(1.0, (sim + 1) / 2))
    except Exception as exc:
        logger.warning("semantic_similarity failed: %s", exc)
        return _fuzzy_jaccard(expected, actual)


async def _aembed(emb_obj, texts: list[str]) -> list[list[float]]:
    if hasattr(emb_obj, "aembed_documents"):
        return await emb_obj.aembed_documents(texts)
    return emb_obj.embed_documents(texts)


def _fuzzy_jaccard(a: str, b: str) -> float:
    sa = set(re.findall(r"\w+", a.lower()))
    sb = set(re.findall(r"\w+", b.lower()))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


@lru_cache(maxsize=1)
def _judge_llm():
    try:
        from llm import get_judge_model

        return get_judge_model(temperature=0.0)
    except Exception:
        return None


def _has_valid_key() -> bool:
    from llm import is_llm_configured

    return is_llm_configured()


def _parse_score(raw: str) -> Optional[float]:
    match = re.search(r"\{.*\}", raw, re.S)
    if match:
        try:
            data = json.loads(match.group(0))
            v = data.get("score")
            if isinstance(v, (int, float)):
                return max(0.0, min(1.0, float(v)))
        except Exception:
            pass
    m2 = re.search(r"(\d+(?:\.\d+)?)", raw)
    if not m2:
        return None
    val = float(m2.group(1))
    if val > 1:
        val = val / 100.0
    return max(0.0, min(1.0, val))


_FAITH_PROMPT = """你是严格的评估官。根据提供的『参考资料』判断『答案』中陈述的事实是否都能由参考资料支持。
- 不要被风格/措辞影响,只看事实性
- 输出严格 JSON: {{"score": 0.0~1.0, "reason": "..."}}
- 1.0 = 完全可被资料支持; 0.0 = 大部分无依据/编造

问题: {question}
答案: {answer}
参考资料:
{context}
"""


_RELEVANCE_PROMPT = """你是严格的评估官。判断『答案』回答『问题』的相关性与切题程度。
- 输出严格 JSON: {{"score": 0.0~1.0, "reason": "..."}}
- 1.0 = 紧扣问题且充分; 0.0 = 完全跑题/无效

问题: {question}
答案: {answer}
"""


async def faithfulness(question: str, answer: str, context: str) -> Optional[float]:
    if not _has_valid_key():
        return None
    llm = _judge_llm()
    if llm is None:
        return None
    prompt = _FAITH_PROMPT.format(question=question, answer=answer, context=context or "(无)")
    try:
        resp = await llm.ainvoke(prompt)
        return _parse_score(resp.content if hasattr(resp, "content") else str(resp))
    except Exception as exc:
        logger.warning("faithfulness judge failed: %s", exc)
        return None


async def answer_relevance(question: str, answer: str) -> Optional[float]:
    if not _has_valid_key():
        return None
    llm = _judge_llm()
    if llm is None:
        return None
    prompt = _RELEVANCE_PROMPT.format(question=question, answer=answer)
    try:
        resp = await llm.ainvoke(prompt)
        return _parse_score(resp.content if hasattr(resp, "content") else str(resp))
    except Exception as exc:
        logger.warning("relevance judge failed: %s", exc)
        return None
