"""Job requirement skill extraction.

The deterministic lexicon scanner in ``text_utils`` only catches skills it knows
about. Real job descriptions phrase requirements in many ways, so we use the LLM
to read a JD and return a clean, normalised list of required skills/keywords —
mirroring how resumes are parsed. Results are cached on the job so we never pay
the LLM cost twice, and a lexicon fallback keeps things working if the model is
unavailable.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.tools import text_utils as tu

logger = get_logger(__name__)

_SYSTEM = (
    "You are an expert technical recruiter. Extract the concrete skills, "
    "technologies, tools, and frameworks a candidate needs for the job. "
    "Return ONLY real, specific skills (e.g. 'python', 'kubernetes', 'react', "
    "'rest apis') — never sentences, soft phrases, or company names. "
    'Respond as JSON: {"skills": ["...", "..."]}.'
)


def extract_job_skills(
    description: str,
    title: str = "",
    existing: list[str] | None = None,
) -> list[str]:
    """Return a normalised list of skills required by a job.

    Strategy: combine any pre-supplied skills (e.g. from the job board) with
    LLM-extracted skills, falling back to the lexicon scanner. Everything is
    normalised and de-duplicated.
    """
    # Lazy import avoids a circular import (agents.base -> tools).
    from app.agents.base import llm_json

    skills: set[str] = tu.normalize_skills(existing or [])

    text = (description or "").strip()
    if text:
        result = llm_json(
            _SYSTEM,
            f"Job title: {title}\n\nJob description:\n{text[:6000]}",
            temperature=0.0,
            fallback=None,
        )
        if isinstance(result, dict) and isinstance(result.get("skills"), list):
            skills |= tu.normalize_skills(result["skills"])
        else:
            logger.warning("job_skills.llm_fallback")

    # Always union the deterministic lexicon scan as a safety net.
    skills |= tu.extract_skills(text)

    # Drop overly generic single-letter / noise tokens.
    cleaned = {s for s in skills if len(s) > 1}
    return sorted(cleaned)


def skills_for_job(job: dict) -> set[str]:
    """Resolve required skills for an in-flight job dict (pipeline use).

    Prefers a clean pre-supplied skill list; otherwise extracts from the
    description. Returns a normalised set.
    """
    existing = list(job.get("skills") or [])
    needs_extraction = not existing or any(len(s.split()) > 4 for s in existing)
    if needs_extraction and (job.get("description") or "").strip():
        return set(
            extract_job_skills(
                job.get("description") or "", job.get("title") or "", existing
            )
        )
    return tu.normalize_skills(existing)
