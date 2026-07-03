"""Agent 4 — ATS Scoring Agent.

Computes an explainable 0-100 ATS score for the target job (or the top ranked
job). Delegates math to the deterministic ATS engine; the agent's job is to
pick the target and shape the output for the state.
"""
from __future__ import annotations

from app.agents.base import track
from app.agents.state import TalentTrailState
from app.tools import ats_engine, job_skills, text_utils as tu


def _resolve_target(state: TalentTrailState) -> dict | None:
    target_id = state.get("target_job_id")
    pools = (state.get("jobs_found") or []) + [
        r.get("job") for r in (state.get("ranked_jobs") or []) if r.get("job")
    ]
    if target_id is not None:
        for job in pools:
            if job and job.get("id") == target_id:
                return job
    ranked = state.get("ranked_jobs") or []
    if ranked:
        return ranked[0].get("job")
    return pools[0] if pools else None


@track("ats_scoring")
def ats_scoring_node(state: TalentTrailState) -> dict:
    resume = state.get("resume_data") or {}
    job = _resolve_target(state)
    if not resume or not job:
        return {"ats_scores": {}}

    job_skill_set = job_skills.skills_for_job(job)
    resume_skill_set = tu.normalize_skills(resume.get("skills") or [])
    resume_skill_set |= tu.extract_skills(
        resume.get("raw_text") or ats_engine._resume_to_text(resume)
    )
    breakdown = ats_engine.score(
        resume, job.get("description") or "",
        job_skills=job_skill_set, resume_skills=resume_skill_set,
    )
    return {
        "ats_scores": {
            "job_id": job.get("id"),
            "total_score": breakdown.total_score,
            "skills_match": breakdown.skills_match,
            "projects_match": breakdown.projects_match,
            "experience_match": breakdown.experience_match,
            "education_match": breakdown.education_match,
            "keyword_density": breakdown.keyword_density,
            "breakdown": breakdown.detail,
        }
    }
