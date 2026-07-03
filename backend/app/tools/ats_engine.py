"""ATS Scoring Engine.

Produces an explainable 0-100 score. Weights are configurable and documented so
the score is defensible (a key portfolio differentiator vs. a black box).

    total = 0.40 * skills_match
          + 0.20 * projects_match
          + 0.20 * experience_match
          + 0.10 * education_match
          + 0.10 * keyword_density

Each sub-score is in 0..1; the engine returns both the weighted total (0..100)
and a transparent breakdown for the UI's "Explainable ATS" card.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.tools import text_utils as tu


@dataclass
class ATSWeights:
    skills: float = 0.40
    projects: float = 0.20
    experience: float = 0.20
    education: float = 0.10
    keyword_density: float = 0.10


@dataclass
class ATSBreakdown:
    skills_match: float
    projects_match: float
    experience_match: float
    education_match: float
    keyword_density: float
    total_score: float
    detail: dict = field(default_factory=dict)


_EDU_LEVELS = ["high school", "associate", "bachelor", "master", "phd", "doctor"]


def _experience_match(resume: dict, job_text: str) -> float:
    """Compare required years (parsed from JD) to candidate years."""
    import re

    req = re.search(r"(\d+)\+?\s*years?", job_text.lower())
    required_years = int(req.group(1)) if req else 0
    candidate_years = float(resume.get("years_of_experience") or 0)
    if required_years == 0:
        return 1.0 if candidate_years > 0 else 0.6
    return max(0.0, min(1.0, candidate_years / required_years))


def _education_match(resume: dict, job_text: str) -> float:
    job_l = job_text.lower()
    required = max((i for i, lvl in enumerate(_EDU_LEVELS) if lvl in job_l), default=-1)
    edu_text = " ".join(str(e) for e in (resume.get("education") or [])).lower()
    candidate = max((i for i, lvl in enumerate(_EDU_LEVELS) if lvl in edu_text), default=-1)
    if required < 0:
        return 1.0
    if candidate < 0:
        return 0.3
    return 1.0 if candidate >= required else 0.6


def _projects_match(resume: dict, job_skills: set[str]) -> float:
    projects = resume.get("projects") or []
    if not projects or not job_skills:
        return 0.5 if projects else 0.0
    project_text = " ".join(
        f"{p.get('name','')} {p.get('description','')} {' '.join(p.get('tech_stack') or [])}"
        for p in projects
    )
    project_skills = tu.extract_skills(project_text)
    return tu.coverage(project_skills, job_skills)


def score(
    resume: dict,
    job_text: str,
    weights: ATSWeights | None = None,
    *,
    job_skills: set[str] | None = None,
    resume_skills: set[str] | None = None,
) -> ATSBreakdown:
    """Compute the ATS score for a parsed resume against a job description.

    ``job_skills``/``resume_skills`` may be supplied (e.g. LLM-extracted) for
    richer matching; otherwise they are derived from the text via the lexicon.
    """
    w = weights or ATSWeights()

    resume_text = resume.get("raw_text") or _resume_to_text(resume)
    if resume_skills is None:
        resume_skills = tu.normalize_skills(resume.get("skills") or [])
        resume_skills |= tu.extract_skills(resume_text)
    if job_skills is None:
        job_skills = tu.extract_skills(job_text)

    # Coverage = how many of the job's required skills the resume satisfies.
    # This is the intuitive, ATS-relevant metric (vs. breadth-penalising Jaccard).
    skills_match = tu.coverage(resume_skills, job_skills) if job_skills else 0.0
    projects_match = _projects_match(resume, job_skills)
    experience_match = _experience_match(resume, job_text)
    education_match = _education_match(resume, job_text)
    kw_density = tu.keyword_density(resume_text, job_text)

    total = (
        w.skills * skills_match
        + w.projects * projects_match
        + w.experience * experience_match
        + w.education * education_match
        + w.keyword_density * kw_density
    ) * 100.0

    return ATSBreakdown(
        skills_match=round(skills_match, 4),
        projects_match=round(projects_match, 4),
        experience_match=round(experience_match, 4),
        education_match=round(education_match, 4),
        keyword_density=round(kw_density, 4),
        total_score=round(total, 2),
        detail={
            "matched_skills": sorted(resume_skills & job_skills),
            "missing_skills": sorted(job_skills - resume_skills),
            "weights": w.__dict__,
        },
    )


def _resume_to_text(resume: dict) -> str:
    parts = [
        resume.get("summary", ""),
        " ".join(map(str, resume.get("skills") or [])),
        " ".join(
            f"{p.get('name','')} {p.get('description','')}"
            for p in (resume.get("projects") or [])
        ),
        " ".join(map(str, resume.get("education") or [])),
        " ".join(map(str, resume.get("experience") or [])),
    ]
    return " ".join(parts)
