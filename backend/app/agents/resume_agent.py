"""Agent 1 — Resume Analysis Agent.

Turns raw resume text into structured Resume JSON. Uses the LLM for semantic
extraction, but always backstops with deterministic skill extraction so the
output is never empty even if the LLM is unavailable.
"""
from __future__ import annotations

from app.agents.base import llm_json, track
from app.agents.state import TalentTrailState
from app.tools import text_utils as tu

_SYSTEM = (
    "You are an expert technical recruiter and resume parser. "
    "Extract structured data from the resume. Respond with ONLY valid JSON "
    "using this schema: {"
    '"name": str, "summary": str, "skills": [str], '
    '"education": [{"degree": str, "institution": str, "year": str}], '
    '"experience": [{"title": str, "company": str, "duration": str, "highlights": [str]}], '
    '"projects": [{"name": str, "description": str, "tech_stack": [str]}], '
    '"internships": [str], "achievements": [str], '
    '"years_of_experience": number}. '
    "Never invent experience that is not in the text."
)


@track("resume_analysis")
def resume_analysis_node(state: TalentTrailState) -> dict:
    resume = dict(state.get("resume_data") or {})
    raw_text = resume.get("raw_text", "")
    if not raw_text:
        return {"resume_data": resume}

    parsed = llm_json(_SYSTEM, raw_text[:12000], fallback={}) or {}

    # Deterministic safety net: ensure skills are populated.
    detected = sorted(tu.extract_skills(raw_text))
    parsed.setdefault("skills", [])
    merged_skills = sorted({*map(str.lower, parsed["skills"]), *detected})
    parsed["skills"] = merged_skills
    parsed.setdefault("projects", [])
    parsed.setdefault("education", [])
    parsed.setdefault("experience", [])
    parsed.setdefault("summary", raw_text[:300])
    parsed["raw_text"] = raw_text

    return {"resume_data": parsed}
