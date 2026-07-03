"""Agent 8 — Career Strategy Agent.

Synthesises the whole run (resume + market jobs + gaps) into a personalised
strategy: target roles, skills to learn, projects to build, certifications, and
a phased roadmap.
"""
from __future__ import annotations

from app.agents.base import llm_json, track
from app.agents.state import TalentTrailState

_SYSTEM = (
    "You are a senior career coach for software/AI roles. Using the candidate "
    "profile and the in-demand skills from current job postings, produce a "
    "concrete growth plan. Respond with ONLY JSON: {"
    '"target_roles": [str], "skills_to_learn": [str], '
    '"projects_to_build": [str], "certifications": [str], '
    '"roadmap": {"30_days": [str], "60_days": [str], "90_days": [str]}}.'
)


@track("career_strategy")
def career_strategy_node(state: TalentTrailState) -> dict:
    resume = state.get("resume_data") or {}
    ranked = state.get("ranked_jobs") or []

    market_skills: list[str] = []
    for r in ranked[:10]:
        job = r.get("job") or {}
        market_skills.extend(job.get("skills") or [])

    user = (
        f"CANDIDATE SKILLS: {', '.join(map(str, resume.get('skills') or []))}\n"
        f"CANDIDATE SUMMARY: {resume.get('summary','')}\n"
        f"IN-DEMAND SKILLS FROM MATCHED JOBS: {', '.join(sorted(set(market_skills)))}\n"
    )
    fallback = {
        "target_roles": ["Backend Engineer", "ML Engineer"],
        "skills_to_learn": sorted(set(market_skills))[:5] or ["docker", "aws"],
        "projects_to_build": ["Ship an end-to-end LLM app with evaluation"],
        "certifications": ["AWS Certified Developer"],
        "roadmap": {
            "30_days": ["Close top 3 skill gaps"],
            "60_days": ["Build a portfolio project"],
            "90_days": ["Apply to 20 tailored roles"],
        },
    }
    result = llm_json(_SYSTEM, user, temperature=0.4, fallback=fallback) or fallback
    return {"recommendations": result}
