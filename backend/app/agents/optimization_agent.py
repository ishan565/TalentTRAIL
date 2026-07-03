"""Agent 6 — Resume Optimization Agent.

Rewrites bullets and summary to be ATS-friendly and tailored to the target job,
weaving in the *missing* keywords the candidate genuinely has context for.

Guardrail: the system prompt forbids inventing experience. We only rephrase or
surface existing content — never fabricate roles, employers, or metrics.
"""
from __future__ import annotations

from app.agents.base import llm_json, track
from app.agents.state import TalentTrailState
from app.agents.ats_agent import _resolve_target

_SYSTEM = (
    "You are an expert resume writer specialising in ATS optimisation. "
    "Rewrite the candidate's resume content to target the given job WITHOUT "
    "inventing any experience, employer, metric, or skill the candidate does "
    "not already have. Use strong action verbs and quantify only where the "
    "original already implies numbers. Respond with ONLY JSON: "
    '{"optimized_bullets": [str], "improved_summary": str, "notes": [str]}.'
)


@track("resume_optimization")
def resume_optimization_node(state: TalentTrailState) -> dict:
    resume = state.get("resume_data") or {}
    job = _resolve_target(state)
    if not resume:
        return {"optimized_resume": {}}

    missing = state.get("missing_keywords") or {}
    user = (
        f"JOB TITLE: {job.get('title') if job else 'N/A'}\n"
        f"JOB DESCRIPTION:\n{(job.get('description') if job else '')[:3000]}\n\n"
        f"CANDIDATE SUMMARY: {resume.get('summary','')}\n"
        f"CANDIDATE SKILLS: {', '.join(map(str, resume.get('skills') or []))}\n"
        f"CANDIDATE PROJECTS: {resume.get('projects')}\n"
        f"MISSING KEYWORDS TO ADDRESS (only if candidate truly has them): {missing.get('missing')}\n"
    )

    fallback = {
        "optimized_bullets": [
            f"Built and shipped features using {', '.join((resume.get('skills') or ['relevant tools'])[:4])}.",
        ],
        "improved_summary": resume.get("summary", ""),
        "notes": ["LLM unavailable — returned baseline content."],
    }
    result = llm_json(_SYSTEM, user, temperature=0.3, fallback=fallback) or fallback
    return {"optimized_resume": result}
