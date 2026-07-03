"""LangGraph shared state.

The state is a ``TypedDict`` (LangGraph's recommended channel type). Every agent
node receives the whole state and returns a partial update; LangGraph merges the
returned keys back in. Keeping one rich state object means agents compose freely
and we get a complete execution trace for free.

Field reference
---------------
user_id            : owner of this run (authz + persistence).
resume_data        : structured Resume JSON from the Resume Analysis Agent.
job_query          : the user's search intent (role/keywords).
location           : optional location filter.
jobs_found         : raw, deduplicated postings from the Job Discovery Agent.
ranked_jobs        : jobs + scores from the Semantic Matching Agent (sorted).
ats_scores         : per-job ATS breakdowns from the ATS Scoring Agent.
missing_keywords   : per-job categorised gaps from the Missing Keyword Agent.
optimized_resume   : rewritten bullets/summary from the Optimization Agent.
cover_letters      : generated letters keyed by job id.
applications       : tracked application records (status board).
recommendations    : career strategy/roadmap output.
target_job_id      : focus job for single-job flows (ATS/keywords/cover letter).
execution_history  : ordered list of {agent, status, ms, note} for observability.
errors             : non-fatal errors collected per agent (graph keeps running).
"""
from __future__ import annotations

from typing import Annotated, Any, Optional, TypedDict
from operator import add


class TalentTrailState(TypedDict, total=False):
    # ---- inputs ----
    user_id: int
    job_query: str
    location: Optional[str]
    target_job_id: Optional[int]
    company_type: str

    # ---- resume ----
    resume_data: dict[str, Any]
    optimized_resume: dict[str, Any]

    # ---- discovery & matching ----
    jobs_found: list[dict[str, Any]]
    ranked_jobs: list[dict[str, Any]]

    # ---- analysis ----
    ats_scores: dict[str, Any]
    missing_keywords: dict[str, Any]

    # ---- generation ----
    cover_letters: dict[str, str]
    recommendations: dict[str, Any]

    # ---- tracking ----
    applications: list[dict[str, Any]]

    # ---- observability (reducer = list concat so nodes append) ----
    execution_history: Annotated[list[dict[str, Any]], add]
    errors: Annotated[list[dict[str, Any]], add]


def new_state(user_id: int, **kwargs) -> TalentTrailState:
    base: TalentTrailState = {
        "user_id": user_id,
        "company_type": "startup",
        "execution_history": [],
        "errors": [],
    }
    base.update(kwargs)  # type: ignore[arg-type]
    return base
