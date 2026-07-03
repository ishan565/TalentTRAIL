"""ATS scoring, keyword gap, resume optimization, and cover letter endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import (
    ATSRequest,
    ATSResult,
    CoverLetterRequest,
    CoverLetterResult,
    KeywordRequest,
    KeywordResult,
    OptimizeRequest,
    OptimizeResult,
)
from app.services import copilot_service as svc

router = APIRouter(tags=["analysis"])


@router.post("/ats/score", response_model=ATSResult)
def ats_score(
    payload: ATSRequest,
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return svc.compute_ats(db, current, payload.resume_id, payload.job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/keywords/analyze", response_model=KeywordResult)
def keyword_analyze(
    payload: KeywordRequest,
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return svc.compute_keywords(db, current, payload.resume_id, payload.job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/resume/optimize", response_model=OptimizeResult)
def optimize(
    payload: OptimizeRequest,
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return svc.optimize_resume(db, current, payload.resume_id, payload.job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/cover-letter/generate", response_model=CoverLetterResult)
def cover_letter(
    payload: CoverLetterRequest,
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        content = svc.generate_cover_letter(
            db, current, payload.resume_id, payload.job_id, payload.company_type
        )
        return CoverLetterResult(content=content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
