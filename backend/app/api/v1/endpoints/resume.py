"""Resume endpoints: upload, analyze, list, active."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db import models
from app.db.session import get_db
from app.schemas import ResumeOut
from app.services import copilot_service as svc

router = APIRouter(prefix="/resume", tags=["resume"])

_ALLOWED = {".pdf", ".docx", ".doc", ".txt", ".md"}


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # --- file upload validation (security) ---
    import os

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED:
        raise HTTPException(status_code=400, detail=f"Unsupported file type {ext}")
    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    return svc.create_resume_from_upload(db, current, file.filename, data)


@router.post("/{resume_id}/analyze", response_model=ResumeOut)
def analyze_resume(
    resume_id: int,
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.get(models.Resume, resume_id)
    if not resume or resume.user_id != current.id:
        raise HTTPException(status_code=404, detail="Resume not found")
    return svc.analyze_resume(db, resume)


@router.get("", response_model=list[ResumeOut])
def list_resumes(
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Resume)
        .filter(models.Resume.user_id == current.id)
        .order_by(models.Resume.version.desc())
        .all()
    )


@router.get("/active", response_model=ResumeOut)
def get_active(
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = svc.active_resume(db, current)
    if not resume:
        raise HTTPException(status_code=404, detail="No active resume")
    return resume
