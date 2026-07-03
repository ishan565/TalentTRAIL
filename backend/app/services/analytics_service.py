"""Analytics service: derives dashboard metrics from persisted data."""
from __future__ import annotations

from collections import Counter, defaultdict

from sqlalchemy.orm import Session

from app.db import models


def build_analytics(db: Session, user: models.User) -> dict:
    apps = db.query(models.Application).filter(models.Application.user_id == user.id).all()
    matches = db.query(models.JobMatch).filter(models.JobMatch.user_id == user.id).all()
    keyword_rows = (
        db.query(models.KeywordAnalysis)
        .filter(models.KeywordAnalysis.user_id == user.id)
        .all()
    )

    by_status = Counter(a.status.value for a in apps)
    applied = sum(
        by_status.get(s, 0) for s in ("applied", "oa", "interview", "final_round", "offer")
    )
    interviews = sum(by_status.get(s, 0) for s in ("interview", "final_round", "offer"))
    offers = by_status.get("offer", 0)

    # Applications over time (by day).
    over_time: dict[str, int] = defaultdict(int)
    for a in apps:
        day = (a.applied_at or a.created_at).date().isoformat()
        over_time[day] += 1

    # Top matched skills from job_matches → underlying postings.
    skill_counter: Counter = Counter()
    for m in matches:
        job = db.get(models.JobPosting, m.job_id)
        for s in (job.skills or []) if job else []:
            skill_counter[s] += 1

    # Missing skills aggregated across keyword analyses.
    missing_counter: Counter = Counter()
    for row in keyword_rows:
        for terms in (row.missing or {}).values():
            for t in terms:
                missing_counter[t] += 1

    # Source performance: avg final_score per source.
    src_scores: dict[str, list[float]] = defaultdict(list)
    for m in matches:
        job = db.get(models.JobPosting, m.job_id)
        if job:
            src_scores[job.source.value].append(m.final_score)

    return {
        "total_applications": len(apps),
        "by_status": dict(by_status),
        "interview_rate": round(interviews / applied, 3) if applied else 0.0,
        "offer_rate": round(offers / applied, 3) if applied else 0.0,
        "applications_over_time": [
            {"date": d, "count": c} for d, c in sorted(over_time.items())
        ],
        "top_matched_skills": [
            {"skill": s, "count": c} for s, c in skill_counter.most_common(10)
        ],
        "missing_skills": [
            {"skill": s, "count": c} for s, c in missing_counter.most_common(10)
        ],
        "source_performance": [
            {"source": src, "avg_score": round(sum(v) / len(v), 3)}
            for src, v in src_scores.items()
            if v
        ],
    }
