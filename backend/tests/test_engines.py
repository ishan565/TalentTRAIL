"""Unit tests for the deterministic scoring engines (no LLM, no network)."""
from __future__ import annotations

from app.tools import ats_engine, keyword_engine, matching_engine, text_utils


RESUME = {
    "raw_text": "Experienced Python engineer. Built FastAPI services with PostgreSQL and Docker. "
    "Projects using LangChain and embeddings.",
    "skills": ["python", "fastapi", "postgresql", "docker", "langchain"],
    "projects": [
        {"name": "RAG bot", "description": "LLM app", "tech_stack": ["langchain", "chromadb"]}
    ],
    "education": ["Bachelor of Science in Computer Science"],
    "years_of_experience": 3,
}

JOB = (
    "We need a Python engineer with FastAPI, PostgreSQL, Docker, AWS, and Kubernetes. "
    "3+ years experience. Bachelor degree required."
)


def test_extract_skills_finds_known_skills():
    skills = text_utils.extract_skills(JOB)
    assert "python" in skills and "fastapi" in skills and "aws" in skills


def test_ats_score_in_range_and_explained():
    result = ats_engine.score(RESUME, JOB)
    assert 0 <= result.total_score <= 100
    assert "matched_skills" in result.detail
    assert "missing_skills" in result.detail
    # AWS/Kubernetes missing from resume
    assert "aws" in result.detail["missing_skills"]


def test_keyword_engine_categorises_missing():
    analysis = keyword_engine.analyze(RESUME["raw_text"], JOB)
    assert "python" in analysis["present"]
    flat_missing = sum(analysis["missing"].values(), [])
    assert "aws" in flat_missing


def test_matching_engine_ranks_relevant_higher():
    jobs = [
        {"id": 1, "title": "Python Backend", "description": JOB, "posted_at": None},
        {"id": 2, "title": "Marketing Manager", "description": "SEO, ads, copywriting", "posted_at": None},
    ]
    ranked = matching_engine.rank(RESUME, jobs)
    assert ranked[0].job_id == 1
    assert ranked[0].final_score >= ranked[1].final_score


def test_cosine_bounds():
    assert text_utils.cosine([1, 0], [1, 0]) == 1.0
    assert text_utils.cosine([1, 0], [0, 1]) == 0.0
