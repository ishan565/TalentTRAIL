"""Agent 9 — Application Tracker Agent.

Within the graph this agent summarises the candidate's application pipeline and
computes funnel analytics. The authoritative CRUD for applications lives in the
service/API layer; here we derive insights from whatever the state carries.
"""
from __future__ import annotations

from collections import Counter

from app.agents.base import track
from app.agents.state import TalentTrailState

_FUNNEL = ["saved", "applied", "oa", "interview", "final_round", "offer"]


@track("application_tracker")
def application_tracker_node(state: TalentTrailState) -> dict:
    apps = state.get("applications") or []
    by_status = Counter(a.get("status", "saved") for a in apps)
    total = len(apps)
    applied = by_status.get("applied", 0) + by_status.get("oa", 0) + by_status.get(
        "interview", 0
    ) + by_status.get("final_round", 0) + by_status.get("offer", 0)
    interviews = by_status.get("interview", 0) + by_status.get("final_round", 0) + by_status.get("offer", 0)
    offers = by_status.get("offer", 0)

    analytics = {
        "total": total,
        "by_status": {s: by_status.get(s, 0) for s in _FUNNEL + ["rejected", "withdrawn"]},
        "interview_rate": round(interviews / applied, 3) if applied else 0.0,
        "offer_rate": round(offers / applied, 3) if applied else 0.0,
    }
    return {"applications": apps, "recommendations": {**(state.get("recommendations") or {}), "pipeline": analytics}}
