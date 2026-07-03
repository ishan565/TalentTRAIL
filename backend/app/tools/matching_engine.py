"""Job Matching Engine — 4-stage weighted ranking.

    Stage 1: Keyword match   (Jaccard over content keywords)
    Stage 2: Semantic match  (cosine over embeddings)
    Stage 3: ATS match       (reuses the ATS engine, normalised 0..1)
    Stage 4: Weighted ranking + recency

    final = 0.25*keyword + 0.35*semantic + 0.25*ats + 0.15*recency

Weights live in ``MatchWeights`` so they are configurable per deployment / A-B
test. Every score is returned with an explanation for "Explainable ranking".
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.llm import get_embeddings
from app.tools import ats_engine
from app.tools import text_utils as tu
from app.tools import job_skills as job_skills_tool


@dataclass
class MatchWeights:
    keyword: float = 0.25
    semantic: float = 0.35
    ats: float = 0.25
    recency: float = 0.15


@dataclass
class MatchResult:
    job_id: int | str
    keyword_score: float
    semantic_score: float
    ats_score: float
    recency_score: float
    final_score: float
    explanation: dict


def _recency(posted_at: datetime | None, half_life_days: float = 14.0) -> float:
    """Exponential decay: fresh jobs score ~1.0, old jobs decay toward 0."""
    if not posted_at:
        return 0.5
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - posted_at).total_seconds() / 86400.0
    return float(0.5 ** (age_days / half_life_days))


def rank(
    resume: dict,
    jobs: list[dict],
    weights: MatchWeights | None = None,
) -> list[MatchResult]:
    """Rank jobs for a parsed resume. ``jobs`` are dicts with id/description/posted_at."""
    w = weights or MatchWeights()
    resume_text = resume.get("raw_text") or ats_engine._resume_to_text(resume)
    resume_kw = tu.keywords(resume_text)

    embeddings = get_embeddings()
    resume_vec = embeddings.embed_query(resume_text)
    job_texts = [j.get("description") or j.get("title", "") for j in jobs]
    job_vecs = embeddings.embed_documents(job_texts) if job_texts else []

    results: list[MatchResult] = []
    resume_skill_set = tu.normalize_skills(resume.get("skills") or [])
    resume_skill_set |= tu.extract_skills(resume_text)
    for idx, (job, job_vec) in enumerate(zip(jobs, job_vecs)):
        job_text = job.get("description") or job.get("title", "")
        keyword_score = tu.jaccard(resume_kw, tu.keywords(job_text))
        semantic_score = max(0.0, tu.cosine(resume_vec, job_vec))
        # Use rich skill sets for an accurate ATS score inside ranking.
        job_skill_set = job_skills_tool.skills_for_job(job)
        ats = ats_engine.score(
            resume, job_text, job_skills=job_skill_set, resume_skills=resume_skill_set
        ).total_score / 100.0
        recency_score = _recency(job.get("posted_at"))

        final = (
            w.keyword * keyword_score
            + w.semantic * semantic_score
            + w.ats * ats
            + w.recency * recency_score
        )
        # ``id`` exists once persisted; fall back to external_id/index otherwise.
        job_id = job.get("id") or job.get("external_id") or idx
        results.append(
            MatchResult(
                job_id=job_id,
                keyword_score=round(keyword_score, 4),
                semantic_score=round(semantic_score, 4),
                ats_score=round(ats, 4),
                recency_score=round(recency_score, 4),
                final_score=round(final, 4),
                explanation={
                    "weights": w.__dict__,
                    "why": _explain(keyword_score, semantic_score, ats, recency_score),
                },
            )
        )

    results.sort(key=lambda r: r.final_score, reverse=True)
    return results


def _explain(kw: float, sem: float, ats: float, rec: float) -> str:
    drivers = sorted(
        {"keyword": kw, "semantic": sem, "ATS": ats, "recency": rec}.items(),
        key=lambda kv: kv[1],
        reverse=True,
    )
    top = drivers[0][0]
    return f"Strongest signal: {top}. Semantic={sem:.2f}, ATS={ats:.2f}, keyword={kw:.2f}."
