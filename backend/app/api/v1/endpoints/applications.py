"""Application tracker endpoints (Kanban CRUD + status transitions)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdate,
    ManualApplicationCreate,
)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationOut, status_code=201)
def create_application(
    payload: ApplicationCreate,
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not db.get(models.JobPosting, payload.job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    app = models.Application(
        user_id=current.id,
        job_id=payload.job_id,
        status=payload.status,
        notes=payload.notes,
        applied_at=datetime.now(timezone.utc)
        if payload.status == models.ApplicationStatus.APPLIED
        else None,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.post("/manual", response_model=ApplicationOut, status_code=201)
def create_manual_application(
    payload: ManualApplicationCreate,
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a job posting from typed details and track it in one step."""
    job = models.JobPosting(
        source=models.JobSource.MANUAL,
        title=payload.title.strip(),
        company=payload.company.strip(),
        location=(payload.location or "").strip() or None,
        url=(payload.url or "").strip() or None,
    )
    db.add(job)
    db.flush()  # assign job.id without a second round-trip
    app = models.Application(
        user_id=current.id,
        job_id=job.id,
        status=payload.status,
        notes=payload.notes,
        applied_at=datetime.now(timezone.utc)
        if payload.status == models.ApplicationStatus.APPLIED
        else None,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Application)
        .filter(models.Application.user_id == current.id)
        .order_by(models.Application.updated_at.desc())
        .all()
    )


@router.patch("/{app_id}", response_model=ApplicationOut)
def update_application(
    app_id: int,
    payload: ApplicationUpdate,
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.get(models.Application, app_id)
    if not app or app.user_id != current.id:
        raise HTTPException(status_code=404, detail="Application not found")
    if payload.status is not None:
        app.status = payload.status
        if payload.status == models.ApplicationStatus.APPLIED and not app.applied_at:
            app.applied_at = datetime.now(timezone.utc)
    if payload.notes is not None:
        app.notes = payload.notes
    db.commit()
    db.refresh(app)
    return app


@router.delete("/{app_id}", status_code=204)
def delete_application(
    app_id: int,
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.get(models.Application, app_id)
    if not app or app.user_id != current.id:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(app)
    db.commit()
