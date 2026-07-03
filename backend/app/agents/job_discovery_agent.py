"""Agent 2 — Job Discovery Agent.

Searches the abstracted job-source layer, aggregates, deduplicates, and
lightly categorises postings. Persistence to the DB happens in the service
layer; the agent stays pure (state in, state out) for testability.
"""
from __future__ import annotations

from app.agents.base import track
from app.agents.state import TalentTrailState
from app.tools import job_sources


def _categorise(job: dict) -> str:
    title = (job.get("title") or "").lower()
    if any(k in title for k in ("ml", "machine learning", "ai", "data")):
        return "ai_ml"
    if any(k in title for k in ("frontend", "react", "ui")):
        return "frontend"
    if any(k in title for k in ("backend", "python", "api")):
        return "backend"
    if "full" in title:
        return "fullstack"
    return "other"


@track("job_discovery")
def job_discovery_node(state: TalentTrailState) -> dict:
    query = state.get("job_query") or ""
    if not query:
        return {"jobs_found": []}

    jobs = job_sources.aggregate(
        query=query,
        location=state.get("location"),
        sources=None,
        limit=30,
        internships=bool(state.get("internships")),
    )
    for job in jobs:
        job["category"] = _categorise(job)
    return {"jobs_found": jobs}
