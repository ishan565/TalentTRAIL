"""Missing-Keyword Engine.

Compares resume vs. job description and returns missing items categorised by
type (skills / technologies / frameworks / tools) and ranked by importance
(how prominently the term appears in the JD).
"""
from __future__ import annotations

from app.tools import text_utils as tu

# Coarse category mapping for the curated lexicon.
_FRAMEWORKS = {
    "fastapi", "flask", "django", "react", "vue", "angular", "express",
    "next.js", "langchain", "langgraph", "pytorch", "tensorflow",
    "scikit-learn", "sqlalchemy",
}
_TOOLS = {"docker", "kubernetes", "terraform", "git", "kafka", "redis", "ci/cd"}
_TECHNOLOGIES = {
    "aws", "gcp", "azure", "postgresql", "mysql", "mongodb", "graphql", "grpc",
    "rest", "chromadb", "pinecone", "embeddings", "rag", "vector database",
    "semantic search", "microservices",
}


def _categorise(term: str) -> str:
    if term in _FRAMEWORKS:
        return "frameworks"
    if term in _TOOLS:
        return "tools"
    if term in _TECHNOLOGIES:
        return "technologies"
    return "skills"


def analyze(
    resume_text: str,
    job_text: str,
    *,
    resume_skills: set[str] | None = None,
    job_skills: set[str] | None = None,
) -> dict:
    """Return present + categorised missing keywords with importance ordering.

    ``resume_skills``/``job_skills`` may be supplied (e.g. LLM-extracted) for
    richer matching; otherwise they are derived from the text via the lexicon.
    """
    if resume_skills is None:
        resume_skills = tu.extract_skills(resume_text)
    if job_skills is None:
        job_skills = tu.extract_skills(job_text)

    present = sorted(resume_skills & job_skills)
    missing_terms = job_skills - resume_skills

    tf = tu.term_frequencies(job_text)

    categorised: dict[str, list[str]] = {
        "skills": [], "technologies": [], "frameworks": [], "tools": []
    }
    for term in missing_terms:
        categorised[_categorise(term)].append(term)

    # Rank within each category by frequency in the JD (importance proxy).
    for cat, terms in categorised.items():
        terms.sort(key=lambda t: tf.get(t.split()[0], 0), reverse=True)

    return {"present": present, "missing": categorised}
