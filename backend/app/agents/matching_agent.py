"""Agent 3 — Semantic Matching Agent.

Ranks discovered jobs against the resume using the 4-stage weighted engine
(keyword + semantic + ATS + recency). Output feeds the recommendations UI.
"""
from __future__ import annotations

from dataclasses import asdict

from app.agents.base import track
from app.agents.state import TalentTrailState
from app.tools import matching_engine


@track("semantic_matching")
def semantic_matching_node(state: TalentTrailState) -> dict:
    resume = state.get("resume_data") or {}
    jobs = state.get("jobs_found") or []
    if not resume or not jobs:
        return {"ranked_jobs": []}

    results = matching_engine.rank(resume, jobs)
    # Map using the same id fallback the engine uses (id → external_id → index)
    # so every ranked entry keeps its job reference even before persistence.
    by_id: dict = {}
    for idx, j in enumerate(jobs):
        key = j.get("id") or j.get("external_id") or idx
        by_id[key] = j

    ranked = []
    for r in results:
        ranked.append({**asdict(r), "job": by_id.get(r.job_id)})
    return {"ranked_jobs": ranked}
