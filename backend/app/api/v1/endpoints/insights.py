"""Analytics, career roadmap, and full-pipeline orchestration endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.agents.state import new_state
from app.agents.strategy_agent import career_strategy_node
from app.db import models
from app.db.session import get_db
from app.schemas import AnalyticsOut, RoadmapResult
from app.services import analytics_service, copilot_service as svc

router = APIRouter(tags=["insights"])


@router.get("/analytics", response_model=AnalyticsOut)
def analytics(
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return analytics_service.build_analytics(db, current)


@router.get("/career-roadmap", response_model=RoadmapResult)
def career_roadmap(
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = svc.active_resume(db, current)
    matches = (
        db.query(models.JobMatch)
        .filter(models.JobMatch.user_id == current.id)
        .order_by(models.JobMatch.final_score.desc())
        .limit(10)
        .all()
    )
    ranked = []
    for m in matches:
        job = db.get(models.JobPosting, m.job_id)
        if job:
            ranked.append({"job": svc._job_to_dict(job)})

    state = new_state(
        current.id,
        resume_data=resume.parsed if resume else {},
        ranked_jobs=ranked,
    )
    result = career_strategy_node(state).get("recommendations", {})

    # Persist the recommendation snapshot.
    db.add(
        models.CareerRecommendation(
            user_id=current.id,
            target_roles=result.get("target_roles"),
            skills_to_learn=result.get("skills_to_learn"),
            projects_to_build=result.get("projects_to_build"),
            certifications=result.get("certifications"),
            roadmap=result.get("roadmap"),
        )
    )
    db.commit()
    return result


@router.post("/pipeline/run")
def run_pipeline(
    query: str = Query(..., min_length=1, max_length=200),
    location: str | None = None,
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute the full LangGraph multi-agent pipeline end-to-end."""
    return svc.run_full_pipeline(db, current, query, location)
