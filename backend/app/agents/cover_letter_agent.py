"""Agent 7 — Cover Letter Agent.

Generates a personalised, PDF-ready cover letter whose tone adapts to the
company archetype (startup / FAANG / enterprise / AI company).
"""
from __future__ import annotations

from app.agents.base import llm_text, track
from app.agents.state import TalentTrailState
from app.agents.ats_agent import _resolve_target

_TONE = {
    "startup": "energetic, scrappy, ownership-driven; emphasise shipping fast and wearing many hats",
    "faang": "structured, impact- and scale-oriented; emphasise rigor, metrics, and system design",
    "enterprise": "professional, reliability- and process-oriented; emphasise stakeholder collaboration",
    "ai": "research-aware and product-minded; emphasise LLMs, evaluation, and responsible AI",
}

_SYSTEM = (
    "You are an expert career writer. Write a concise (250-350 word), "
    "professional cover letter. Use the requested tone. Do not fabricate "
    "experience. Output plain text suitable for PDF export with a greeting, "
    "3 short body paragraphs, and a sign-off."
)


@track("cover_letter")
def cover_letter_node(state: TalentTrailState) -> dict:
    resume = state.get("resume_data") or {}
    job = _resolve_target(state)
    if not job:
        return {"cover_letters": {}}

    company_type = state.get("company_type", "startup")
    tone = _TONE.get(company_type, _TONE["startup"])
    user = (
        f"TONE: {tone}\n"
        f"COMPANY: {job.get('company')}\n"
        f"ROLE: {job.get('title')}\n"
        f"JOB DESCRIPTION:\n{(job.get('description') or '')[:2500]}\n\n"
        f"CANDIDATE NAME: {resume.get('name','the candidate')}\n"
        f"CANDIDATE SUMMARY: {resume.get('summary','')}\n"
        f"CANDIDATE SKILLS: {', '.join(map(str, resume.get('skills') or []))}\n"
    )
    fallback = (
        f"Dear {job.get('company')} Hiring Team,\n\n"
        f"I am excited to apply for the {job.get('title')} role. "
        "My background aligns closely with your needs.\n\nSincerely,\n"
        f"{resume.get('name','Candidate')}"
    )
    content = llm_text(_SYSTEM, user, temperature=0.6, fallback=fallback)
    return {"cover_letters": {str(job.get("id")): content}}
