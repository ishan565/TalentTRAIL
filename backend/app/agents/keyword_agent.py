"""Agent 5 — Missing Keyword Agent.

Identifies gaps between the resume and the target job, categorised by type and
ranked by importance. Pure delegation to the keyword engine.
"""
from __future__ import annotations

from app.agents.base import track
from app.agents.state import TalentTrailState
from app.agents.ats_agent import _resolve_target
from app.tools import ats_engine, job_skills, keyword_engine, text_utils as tu


@track("missing_keywords")
def missing_keywords_node(state: TalentTrailState) -> dict:
    resume = state.get("resume_data") or {}
    job = _resolve_target(state)
    if not resume or not job:
        return {"missing_keywords": {}}

    resume_text = resume.get("raw_text") or ats_engine._resume_to_text(resume)
    job_skill_set = job_skills.skills_for_job(job)
    resume_skill_set = tu.normalize_skills(resume.get("skills") or [])
    resume_skill_set |= tu.extract_skills(resume_text)
    analysis = keyword_engine.analyze(
        resume_text, job.get("description") or "",
        resume_skills=resume_skill_set, job_skills=job_skill_set,
    )
    analysis["job_id"] = job.get("id")
    return {"missing_keywords": analysis}
