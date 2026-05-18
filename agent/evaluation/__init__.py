"""评测引擎:
- 语义相似度(Embedding cosine)
- Faithfulness(基于检索的事实性 LLM-judge)
- Answer Relevance(LLM-judge,答案与问题相关度)

LangSmith 通过 LANGCHAIN_TRACING_V2=true 自动上报。
"""
from evaluation.engine import EvalResult, evaluate_case

__all__ = ["EvalResult", "evaluate_case"]
