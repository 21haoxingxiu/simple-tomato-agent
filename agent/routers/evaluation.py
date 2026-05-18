from __future__ import annotations

from typing import Optional

import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import AsyncSessionLocal, get_session
from db.models import EvalCase, EvalDataset, EvalRun
from evaluation.engine import evaluate_case
from schemas.eval import (
    BatchSummaryOut,
    CaseCreate,
    CaseOut,
    CaseUpdate,
    DatasetCreate,
    DatasetOut,
    RunBatchRequest,
    RunCaseRequest,
    RunOut,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/eval", tags=["eval"])


def _run_to_out(r: EvalRun) -> RunOut:
    return RunOut(
        id=r.id,
        case_id=r.case_id,
        batch_id=r.batch_id or "",
        actual_answer=r.actual_answer,
        similarity=r.similarity,
        faithfulness=r.faithfulness,
        relevance=r.relevance,
        score=r.score,
        passed=r.passed,
        latency_ms=r.latency_ms,
        citations=r.citations or [],
        error_msg=r.error_msg or "",
        created_at=r.created_at.isoformat(),
    )


async def _latest_run(session: AsyncSession, case_id: str) -> Optional[EvalRun]:
    res = await session.execute(
        select(EvalRun).where(EvalRun.case_id == case_id).order_by(EvalRun.created_at.desc()).limit(1)
    )
    return res.scalar_one_or_none()


# ----- Datasets -----

@router.get("/datasets", response_model=list[DatasetOut])
async def list_datasets(
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(
        select(EvalDataset, func.count(EvalCase.id))
        .outerjoin(EvalCase, EvalCase.dataset_id == EvalDataset.id)
        .where(EvalDataset.workspace_id == x_workspace_id)
        .group_by(EvalDataset.id)
        .order_by(EvalDataset.created_at.desc())
    )
    return [
        DatasetOut(
            id=ds.id,
            name=ds.name,
            description=ds.description,
            case_count=int(cnt or 0),
            created_at=ds.created_at.isoformat(),
        )
        for ds, cnt in res.all()
    ]


@router.post("/datasets", response_model=DatasetOut)
async def create_dataset(
    body: DatasetCreate,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    ds = EvalDataset(workspace_id=x_workspace_id, name=body.name, description=body.description or "")
    session.add(ds)
    await session.commit()
    await session.refresh(ds)
    return DatasetOut(
        id=ds.id,
        name=ds.name,
        description=ds.description,
        case_count=0,
        created_at=ds.created_at.isoformat(),
    )


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    ds = await session.get(EvalDataset, dataset_id)
    if not ds or ds.workspace_id != x_workspace_id:
        raise HTTPException(404, "Dataset not found")
    await session.delete(ds)
    await session.commit()
    return {"ok": True, "deleted_id": dataset_id}


# ----- Cases -----

@router.get("/cases", response_model=list[CaseOut])
async def list_cases(
    x_workspace_id: str = Header(default="default"),
    dataset_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(EvalCase).where(EvalCase.workspace_id == x_workspace_id)
    if dataset_id:
        stmt = stmt.where(EvalCase.dataset_id == dataset_id)
    stmt = stmt.order_by(EvalCase.created_at.desc())
    cases = (await session.execute(stmt)).scalars().all()

    out: list[CaseOut] = []
    for c in cases:
        last = await _latest_run(session, c.id)
        out.append(
            CaseOut(
                id=c.id,
                dataset_id=c.dataset_id,
                question=c.question,
                expected_answer=c.expected_answer,
                tags=c.tags or [],
                latest_run=_run_to_out(last).model_dump() if last else None,
                created_at=c.created_at.isoformat(),
            )
        )
    return out


@router.post("/cases", response_model=CaseOut)
async def create_case(
    body: CaseCreate,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    case = EvalCase(
        workspace_id=x_workspace_id,
        dataset_id=body.dataset_id,
        question=body.question,
        expected_answer=body.expected_answer or "",
        tags=body.tags or [],
    )
    session.add(case)
    await session.commit()
    await session.refresh(case)
    return CaseOut(
        id=case.id,
        dataset_id=case.dataset_id,
        question=case.question,
        expected_answer=case.expected_answer,
        tags=case.tags or [],
        latest_run=None,
        created_at=case.created_at.isoformat(),
    )


@router.patch("/cases/{case_id}", response_model=CaseOut)
async def update_case(
    case_id: str,
    body: CaseUpdate,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    case = await session.get(EvalCase, case_id)
    if not case or case.workspace_id != x_workspace_id:
        raise HTTPException(404, "Case not found")
    if body.question is not None:
        case.question = body.question
    if body.expected_answer is not None:
        case.expected_answer = body.expected_answer
    if body.dataset_id is not None:
        case.dataset_id = body.dataset_id
    if body.tags is not None:
        case.tags = body.tags
    await session.commit()
    await session.refresh(case)
    last = await _latest_run(session, case.id)
    return CaseOut(
        id=case.id,
        dataset_id=case.dataset_id,
        question=case.question,
        expected_answer=case.expected_answer,
        tags=case.tags or [],
        latest_run=_run_to_out(last).model_dump() if last else None,
        created_at=case.created_at.isoformat(),
    )


@router.delete("/cases/{case_id}")
async def delete_case(
    case_id: str,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    case = await session.get(EvalCase, case_id)
    if not case or case.workspace_id != x_workspace_id:
        raise HTTPException(404, "Case not found")
    await session.execute(sa_delete(EvalRun).where(EvalRun.case_id == case_id))
    await session.delete(case)
    await session.commit()
    return {"ok": True, "deleted_id": case_id}


# ----- Run -----

@router.post("/cases/{case_id}/run", response_model=RunOut)
async def run_case(
    case_id: str,
    body: Optional[RunCaseRequest] = None,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    case = await session.get(EvalCase, case_id)
    if not case or case.workspace_id != x_workspace_id:
        raise HTTPException(404, "Case not found")

    kb_id = body.kb_id if body else None
    result = await evaluate_case(
        session=session,
        workspace_id=x_workspace_id,
        question=case.question,
        expected=case.expected_answer,
        kb_id=kb_id,
    )

    run = EvalRun(
        case_id=case.id,
        workspace_id=x_workspace_id,
        kb_id=kb_id,
        actual_answer=result.actual_answer,
        similarity=result.similarity,
        faithfulness=result.faithfulness,
        relevance=result.relevance,
        score=result.score,
        passed=result.passed,
        latency_ms=result.latency_ms,
        citations=result.citations,
        error_msg=result.error_msg,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return _run_to_out(run)


@router.post("/runs/batch", response_model=BatchSummaryOut)
async def run_batch(
    body: RunBatchRequest,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(EvalCase).where(EvalCase.workspace_id == x_workspace_id)
    if body.case_ids:
        stmt = stmt.where(EvalCase.id.in_(body.case_ids))
    elif body.dataset_id:
        stmt = stmt.where(EvalCase.dataset_id == body.dataset_id)
    cases = (await session.execute(stmt)).scalars().all()
    if not cases:
        raise HTTPException(400, "no cases to run")

    batch_id = str(uuid.uuid4())
    runs_out: list[RunOut] = []
    total_score = 0.0
    score_count = 0
    total_latency = 0

    for case in cases:
        # 每个 case 独立 session 防止单个失败影响其他
        async with AsyncSessionLocal() as s:
            try:
                result = await evaluate_case(
                    session=s,
                    workspace_id=x_workspace_id,
                    question=case.question,
                    expected=case.expected_answer,
                    kb_id=body.kb_id,
                )
            except Exception as exc:
                logger.exception("batch run case=%s failed", case.id)
                run = EvalRun(
                    case_id=case.id,
                    workspace_id=x_workspace_id,
                    kb_id=body.kb_id,
                    batch_id=batch_id,
                    actual_answer="",
                    passed=False,
                    error_msg=str(exc)[:1000],
                )
                s.add(run)
                await s.commit()
                await s.refresh(run)
                runs_out.append(_run_to_out(run))
                continue

            run = EvalRun(
                case_id=case.id,
                workspace_id=x_workspace_id,
                kb_id=body.kb_id,
                batch_id=batch_id,
                actual_answer=result.actual_answer,
                similarity=result.similarity,
                faithfulness=result.faithfulness,
                relevance=result.relevance,
                score=result.score,
                passed=result.passed,
                latency_ms=result.latency_ms,
                citations=result.citations,
                error_msg=result.error_msg,
            )
            s.add(run)
            await s.commit()
            await s.refresh(run)
            runs_out.append(_run_to_out(run))

            if result.score is not None:
                total_score += result.score
                score_count += 1
            total_latency += result.latency_ms

    passed = sum(1 for r in runs_out if r.passed)
    return BatchSummaryOut(
        batch_id=batch_id,
        total=len(runs_out),
        passed=passed,
        failed=len(runs_out) - passed,
        avg_score=round(total_score / score_count, 4) if score_count else None,
        avg_latency_ms=int(total_latency / max(1, len(runs_out))),
        runs=runs_out,
    )


@router.get("/cases/{case_id}/runs", response_model=list[RunOut])
async def list_runs(
    case_id: str,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    case = await session.get(EvalCase, case_id)
    if not case or case.workspace_id != x_workspace_id:
        raise HTTPException(404, "Case not found")
    res = await session.execute(
        select(EvalRun).where(EvalRun.case_id == case_id).order_by(EvalRun.created_at.desc())
    )
    return [_run_to_out(r) for r in res.scalars().all()]


@router.get("/summary")
async def workspace_summary(
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    total = (
        await session.execute(
            select(func.count(EvalCase.id)).where(EvalCase.workspace_id == x_workspace_id)
        )
    ).scalar() or 0
    # 取最新一次 run per case
    sub = (
        select(EvalRun.case_id, func.max(EvalRun.created_at).label("ts"))
        .where(EvalRun.workspace_id == x_workspace_id)
        .group_by(EvalRun.case_id)
        .subquery()
    )
    latest_rows = (
        await session.execute(
            select(EvalRun).join(
                sub,
                (EvalRun.case_id == sub.c.case_id) & (EvalRun.created_at == sub.c.ts),
            )
        )
    ).scalars().all()
    passed = sum(1 for r in latest_rows if r.passed)
    avg_score = (
        round(sum(r.score for r in latest_rows if r.score is not None) / max(1, sum(1 for r in latest_rows if r.score is not None)), 4)
        if latest_rows
        else None
    )
    return {
        "total_cases": int(total),
        "evaluated": len(latest_rows),
        "passed": passed,
        "failed": len(latest_rows) - passed,
        "avg_score": avg_score,
    }
