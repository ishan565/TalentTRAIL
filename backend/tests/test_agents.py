"""Tests for individual agent nodes and the LangGraph wiring (no real LLM)."""
from __future__ import annotations

from app.agents.resume_agent import resume_analysis_node
from app.agents.job_discovery_agent import job_discovery_node
from app.agents.matching_agent import semantic_matching_node
from app.agents.ats_agent import ats_scoring_node
from app.agents.state import new_state


def test_resume_node_populates_skills_without_llm():
    state = new_state(1, resume_data={"raw_text": "Python FastAPI Docker PostgreSQL engineer."})
    update = resume_analysis_node(state)
    skills = update["resume_data"]["skills"]
    assert "python" in skills and "docker" in skills


def test_discovery_node_returns_jobs():
    state = new_state(1, job_query="Python Engineer")
    update = job_discovery_node(state)
    assert len(update["jobs_found"]) > 0
    assert "execution_history" in update


def test_matching_then_ats_pipeline():
    state = new_state(
        1,
        job_query="Python Engineer",
        resume_data={
            "raw_text": "Python FastAPI Docker engineer",
            "skills": ["python", "fastapi", "docker"],
            "projects": [],
            "education": [],
        },
    )
    state.update(job_discovery_node(state))
    state.update(semantic_matching_node(state))
    assert len(state["ranked_jobs"]) > 0

    ats_update = ats_scoring_node(state)
    assert 0 <= ats_update["ats_scores"]["total_score"] <= 100
