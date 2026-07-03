"""Service layer: orchestrates agents + persistence.

Endpoints stay thin (validation + HTTP), services own business logic, the DB is
touched only here and in repositories. This keeps the architecture testable and
swappable (clean architecture / service layer pattern).
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.graph import build_graph
from app.agents.state import new_state
from app.core.logging import get_logger
from app.db import models
from app.tools import ats_engine, keyword_engine, matching_engine
from app.tools import job_skills as job_skills_tool
from app.tools import text_utils as tu
from app.tools.document_parser import extract_text

logger = get_logger(__name__)


# --------------------------------------------------------------------------- #
# Resume
# --------------------------------------------------------------------------- #
def create_resume_from_upload(db: Session, user: models.User, filename: str, data: bytes) -> models.Resume:
    raw_text = extract_text(filename, data)

    # New version = previous active count + 1; deactivate old active resume.
    prev = (
        db.query(models.Resume)
        .filter(models.Resume.user_id == user.id)
        .order_by(models.Resume.version.desc())
        .first()
    )
    next_version = (prev.version + 1) if prev else 1
    db.query(models.Resume).filter(
        models.Resume.user_id == user.id, models.Resume.is_active.is_(True)
    ).update({"is_active": False})

    resume = models.Resume(
        user_id=user.id,
        version=next_version,
        is_active=True,
        filename=filename,
        raw_text=raw_text,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def analyze_resume(db: Session, resume: models.Resume) -> models.Resume:
    """Run only the resume-analysis node and persist structured output."""
    from app.agents.resume_agent import resume_analysis_node

    state = new_state(resume.user_id, resume_data={"raw_text": resume.raw_text or ""})
    update = resume_analysis_node(state)
    parsed = update.get("resume_data", {})

    resume.parsed = parsed
    resume.summary = parsed.get("summary")
    # Refresh related skills/projects.
    db.query(models.Skill).filter(models.Skill.resume_id == resume.id).delete()
    db.query(models.Project).filter(models.Project.resume_id == resume.id).delete()
    for s in parsed.get("skills", [])[:100]:
        db.add(models.Skill(resume_id=resume.id, name=str(s)))
    for p in parsed.get("projects", [])[:50]:
        db.add(
            models.Project(
                resume_id=resume.id,
                name=str(p.get("name", "Project")),
                description=p.get("description"),
                tech_stack=p.get("tech_stack"),
            )
        )
    db.commit()
    db.refresh(resume)
    return resume


def active_resume(db: Session, user: models.User) -> models.Resume | None:
    return (
        db.query(models.Resume)
        .filter(models.Resume.user_id == user.id, models.Resume.is_active.is_(True))
        .first()
    )


# --------------------------------------------------------------------------- #
# Jobs: search + persist + rank
# --------------------------------------------------------------------------- #
def search_and_rank_jobs(
    db: Session,
    user: models.User,
    query: str,
    location: str | None,
    limit: int,
    internships: bool = False,
) -> list[dict]:
    from app.tools import job_sources

    found = job_sources.aggregate(
        query=query, location=location, limit=limit, internships=internships
    )
    # Keep raw metadata (internship flag, salary, type) keyed by external_id so
    # we can enrich the persisted/ranked results the frontend receives.
    meta = {
        j.get("external_id"): {
            "is_internship": j.get("is_internship", False),
            "salary": j.get("salary"),
            "job_type": j.get("job_type"),
        }
        for j in found
    }
    persisted = _persist_jobs(db, found)

    def _enrich(job_dict: dict) -> dict:
        extra = meta.get(job_dict.get("external_id"))
        if extra:
            job_dict = {**job_dict, **extra}
        return job_dict

    resume = active_resume(db, user)
    if not resume or not resume.parsed:
        return [
            {"job": _enrich(_job_to_dict(j)), "final_score": 0.0} for j in persisted
        ]

    job_dicts = [_job_to_dict(j) for j in persisted]
    results = matching_engine.rank(resume.parsed, job_dicts)
    by_id = {j["id"]: _enrich(j) for j in job_dicts}

    ranked = []
    for r in results:
        # Persist the match for analytics.
        db.add(
            models.JobMatch(
                user_id=user.id,
                resume_id=resume.id,
                job_id=r.job_id,
                keyword_score=r.keyword_score,
                semantic_score=r.semantic_score,
                ats_score=r.ats_score,
                recency_score=r.recency_score,
                final_score=r.final_score,
                explanation=r.explanation,
            )
        )
        ranked.append(
            {
                "job": by_id.get(r.job_id),
                "final_score": r.final_score,
                "keyword_score": r.keyword_score,
                "semantic_score": r.semantic_score,
                "ats_score": r.ats_score,
                "recency_score": r.recency_score,
                "explanation": r.explanation,
            }
        )
    db.commit()
    return ranked


def _persist_jobs(db: Session, jobs: list[dict]) -> list[models.JobPosting]:
    out: list[models.JobPosting] = []
    for j in jobs:
        existing = (
            db.query(models.JobPosting)
            .filter(models.JobPosting.external_id == j.get("external_id"))
            .first()
        )
        if existing:
            out.append(existing)
            continue
        posting = models.JobPosting(
            external_id=j.get("external_id"),
            source=j.get("source", models.JobSource.MANUAL),
            title=j["title"],
            company=j["company"],
            location=j.get("location"),
            url=j.get("url"),
            description=j.get("description"),
            skills=j.get("skills"),
            posted_at=j.get("posted_at"),
        )
        db.add(posting)
        out.append(posting)
    db.commit()
    for p in out:
        db.refresh(p)
    return out


def _job_to_dict(job: models.JobPosting) -> dict:
    return {
        "id": job.id,
        "external_id": job.external_id,
        "source": job.source,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "url": job.url,
        "description": job.description,
        "skills": job.skills,
        "posted_at": job.posted_at,
    }


# --------------------------------------------------------------------------- #
# Single-job analyses (ATS / keywords / optimize / cover letter)
# --------------------------------------------------------------------------- #
def _require(db: Session, user: models.User, resume_id: int, job_id: int):
    resume = db.get(models.Resume, resume_id)
    job = db.get(models.JobPosting, job_id)
    if not resume or resume.user_id != user.id:
        raise ValueError("Resume not found")
    if not job:
        raise ValueError("Job not found")
    return resume, job


def _resolve_job_skills(db: Session, job: models.JobPosting) -> set[str]:
    """Return the job's required skills, extracting + persisting them if absent.

    Most job boards only give noisy ``job_highlights`` (full sentences), so we
    run the LLM extractor once and cache the clean result on ``job.skills`` for
    reuse by every later analysis.
    """
    existing = list(job.skills or [])
    # Treat a tiny/sentence-y skill list as "needs extraction".
    needs_extraction = not existing or any(len(s.split()) > 4 for s in existing)
    if needs_extraction and (job.description or "").strip():
        extracted = job_skills_tool.extract_job_skills(
            job.description or "", job.title or "", existing
        )
        if extracted:
            job.skills = extracted
            db.add(job)
            db.commit()
            existing = extracted
    return tu.normalize_skills(existing)


def _resume_skill_set(resume: models.Resume) -> set[str]:
    parsed = resume.parsed or {}
    skills = tu.normalize_skills(parsed.get("skills") or [])
    skills |= tu.extract_skills(parsed.get("raw_text") or resume.raw_text or "")
    return skills


def compute_ats(db: Session, user: models.User, resume_id: int, job_id: int) -> dict:
    resume, job = _require(db, user, resume_id, job_id)
    job_skills = _resolve_job_skills(db, job)
    resume_skills = _resume_skill_set(resume)
    b = ats_engine.score(
        resume.parsed or {"raw_text": resume.raw_text},
        job.description or "",
        job_skills=job_skills,
        resume_skills=resume_skills,
    )
    db.add(
        models.ATSScore(
            user_id=user.id, resume_id=resume.id, job_id=job.id,
            skills_match=b.skills_match, projects_match=b.projects_match,
            experience_match=b.experience_match, education_match=b.education_match,
            keyword_density=b.keyword_density, total_score=b.total_score, breakdown=b.detail,
        )
    )
    db.commit()
    return {
        "total_score": b.total_score, "skills_match": b.skills_match,
        "projects_match": b.projects_match, "experience_match": b.experience_match,
        "education_match": b.education_match, "keyword_density": b.keyword_density,
        "breakdown": b.detail,
    }


def compute_keywords(db: Session, user: models.User, resume_id: int, job_id: int) -> dict:
    resume, job = _require(db, user, resume_id, job_id)
    resume_text = (resume.parsed or {}).get("raw_text") or resume.raw_text or ""
    job_skills = _resolve_job_skills(db, job)
    resume_skills = _resume_skill_set(resume)
    analysis = keyword_engine.analyze(
        resume_text, job.description or "",
        resume_skills=resume_skills, job_skills=job_skills,
    )
    db.add(
        models.KeywordAnalysis(
            user_id=user.id, resume_id=resume.id, job_id=job.id,
            missing=analysis["missing"], present=analysis["present"],
        )
    )
    db.commit()
    return analysis


def optimize_resume(db: Session, user: models.User, resume_id: int, job_id: int) -> dict:
    resume, job = _require(db, user, resume_id, job_id)
    from app.agents.optimization_agent import resume_optimization_node

    state = new_state(
        user.id,
        resume_data=resume.parsed or {"raw_text": resume.raw_text},
        jobs_found=[_job_to_dict(job)],
        target_job_id=job.id,
    )
    update = resume_optimization_node(state)
    return update.get("optimized_resume", {})


def generate_cover_letter(
    db: Session, user: models.User, resume_id: int, job_id: int, company_type: str
) -> str:
    resume, job = _require(db, user, resume_id, job_id)
    from app.agents.cover_letter_agent import cover_letter_node

    state = new_state(
        user.id,
        resume_data=resume.parsed or {"raw_text": resume.raw_text},
        jobs_found=[_job_to_dict(job)],
        target_job_id=job.id,
        company_type=company_type,
    )
    update = cover_letter_node(state)
    content = (update.get("cover_letters") or {}).get(str(job.id), "")
    db.add(
        models.CoverLetter(
            user_id=user.id, job_id=job.id, company_type=company_type, content=content
        )
    )
    db.commit()
    return content


# --------------------------------------------------------------------------- #
# Full pipeline (multi-agent orchestration)
# --------------------------------------------------------------------------- #
def run_full_pipeline(db: Session, user: models.User, query: str, location: str | None) -> dict:
    resume = active_resume(db, user)
    run = models.AgentRun(user_id=user.id, graph="full_pipeline", status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    start = time.perf_counter()
    state = new_state(
        user.id,
        job_query=query,
        location=location,
        resume_data=resume.parsed if resume else {"raw_text": ""},
    )
    try:
        final = build_graph().invoke(state)
        run.status = "completed"
        run.execution_history = final.get("execution_history")
    except Exception as exc:  # pragma: no cover
        run.status = "failed"
        run.error = str(exc)
        final = {"errors": [{"error": str(exc)}]}
    finally:
        run.duration_ms = int((time.perf_counter() - start) * 1000)
        db.commit()

    return {
        "ranked_jobs": final.get("ranked_jobs", []),
        "ats_scores": final.get("ats_scores", {}),
        "missing_keywords": final.get("missing_keywords", {}),
        "optimized_resume": final.get("optimized_resume", {}),
        "cover_letters": final.get("cover_letters", {}),
        "recommendations": final.get("recommendations", {}),
        "execution_history": final.get("execution_history", []),
        "run_id": run.id,
    }
