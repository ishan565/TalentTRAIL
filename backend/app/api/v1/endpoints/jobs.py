"""Job endpoints: search and ranked recommendations."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import models
from app.db.session import get_db
from app.services import copilot_service as svc

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/all")
def list_all_jobs(
    limit: int = Query(50, ge=1, le=200),
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """All persisted job postings ordered by newest first.

    Used by analysis pages to populate the job picker before any recommendations
    have been generated (e.g. a fresh user who hasn't run a pipeline yet).
    """
    rows = (
        db.query(models.JobPosting)
        .order_by(models.JobPosting.id.desc())
        .limit(limit)
        .all()
    )
    return {"results": [svc._job_to_dict(j) for j in rows]}


@router.get("/search")
def search_jobs(
    query: str = Query(..., min_length=1, max_length=200),
    location: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    internships: bool = Query(False),
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregate jobs from all sources and rank them against the active resume."""
    return {
        "results": svc.search_and_rank_jobs(
            db, current, query, location, limit, internships
        )
    }


@router.get("/recommendations")
def recommendations(
    limit: int = Query(10, ge=1, le=50),
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Top stored matches for the user, highest final_score first."""
    rows = (
        db.query(models.JobMatch)
        .filter(models.JobMatch.user_id == current.id)
        .order_by(models.JobMatch.final_score.desc())
        .limit(limit)
        .all()
    )
    out = []
    for m in rows:
        job = db.get(models.JobPosting, m.job_id)
        out.append(
            {
                "job": svc._job_to_dict(job) if job else None,
                "final_score": m.final_score,
                "keyword_score": m.keyword_score,
                "semantic_score": m.semantic_score,
                "ats_score": m.ats_score,
                "recency_score": m.recency_score,
                "explanation": m.explanation,
            }
        )
    return {"results": out}


@router.get("/{job_id}")
def get_job(
    job_id: int,
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.get(models.JobPosting, job_id)
    if not job:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Job not found")
    return svc._job_to_dict(job)
