from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class DatasetOut(BaseModel):
    id: str
    name: str
    description: str
    case_count: int = 0
    created_at: str


class CaseCreate(BaseModel):
    question: str
    expected_answer: str = ""
    dataset_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class CaseUpdate(BaseModel):
    question: Optional[str] = None
    expected_answer: Optional[str] = None
    dataset_id: Optional[str] = None
    tags: Optional[list[str]] = None


class CaseOut(BaseModel):
    id: str
    dataset_id: Optional[str]
    question: str
    expected_answer: str
    tags: list[str]
    latest_run: Optional[dict] = None
    created_at: str


class RunCaseRequest(BaseModel):
    kb_id: Optional[str] = None


class RunBatchRequest(BaseModel):
    case_ids: Optional[list[str]] = None
    dataset_id: Optional[str] = None
    kb_id: Optional[str] = None


class RunOut(BaseModel):
    id: str
    case_id: str
    batch_id: str = ""
    actual_answer: str
    similarity: Optional[float]
    faithfulness: Optional[float]
    relevance: Optional[float]
    score: Optional[float]
    passed: bool
    latency_ms: int
    citations: list[dict]
    error_msg: str = ""
    created_at: str


class BatchSummaryOut(BaseModel):
    batch_id: str
    total: int
    passed: int
    failed: int
    avg_score: Optional[float]
    avg_latency_ms: int
    runs: list[RunOut]
