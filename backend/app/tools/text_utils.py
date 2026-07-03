"""Lightweight text utilities shared by the scoring engines.

Deterministic, dependency-free helpers so the matching/ATS engines do not need
an LLM call for their core math. The LLM is used to *enrich* (extract skills,
write prose), while these functions provide the reproducible numbers behind an
explainable score.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable

# A curated skill lexicon used by the deterministic fallback extractor. The
# primary skill source is the LLM (rich, context-aware); this list keeps the
# engines useful when the model is unavailable and powers multi-word matching.
SKILL_LEXICON = {
    # languages
    "python", "java", "javascript", "typescript", "go", "golang", "rust",
    "c++", "c#", "c", "kotlin", "swift", "scala", "ruby", "php", "r", "matlab",
    "bash", "shell", "sql", "nosql",
    # web / backend frameworks
    "fastapi", "flask", "django", "spring", "spring boot", "express",
    "node", "node.js", "nestjs", ".net", "rails", "laravel", "react",
    "react.js", "react native", "vue", "vue.js", "angular", "svelte",
    "next.js", "nuxt", "tailwind", "tailwind css", "bootstrap", "redux",
    "jquery", "html", "css", "sass",
    # data stores
    "postgresql", "postgres", "mysql", "mariadb", "mongodb", "redis",
    "cassandra", "dynamodb", "elasticsearch", "snowflake", "bigquery",
    "oracle", "sqlite", "neo4j",
    # cloud / devops
    "aws", "gcp", "azure", "aws lambda", "s3", "ec2", "terraform", "ansible",
    "docker", "kubernetes", "k8s", "jenkins", "github actions", "gitlab ci",
    "ci/cd", "git", "linux", "unix", "nginx", "kafka", "rabbitmq",
    "prometheus", "grafana", "datadog",
    # ai / ml
    "langchain", "langgraph", "llm", "llms", "rag", "embeddings", "chromadb",
    "pinecone", "weaviate", "pytorch", "tensorflow", "keras", "scikit-learn",
    "sklearn", "pandas", "numpy", "scipy", "opencv", "nlp", "computer vision",
    "hugging face", "transformers", "mlops", "generative ai", "openai",
    "neural networks", "deep learning", "machine learning",
    # apis / arch
    "graphql", "rest", "rest api", "rest apis", "grpc", "microservices",
    "websockets", "oauth", "jwt", "semantic search", "vector database",
    "pydantic", "sqlalchemy", "celery",
    # testing / qa
    "pytest", "junit", "selenium", "cypress", "playwright", "jest",
    "test automation", "automation testing", "qa", "tdd",
    # methods
    "agile", "scrum", "kanban",
}

# Common phrasings in JDs that map to a canonical lexicon skill, so we still
# catch a requirement even when it is worded differently.
_SKILL_ALIASES = {
    "nodejs": "node.js",
    "node js": "node.js",
    "reactjs": "react.js",
    "react js": "react.js",
    "vuejs": "vue.js",
    "nextjs": "next.js",
    "springboot": "spring boot",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "golang": "go",
    "ml": "machine learning",
    "ai/ml": "machine learning",
    "restful": "rest",
    "restful apis": "rest apis",
    "ci cd": "ci/cd",
}

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.\-]*")
_STOPWORDS = {
    "the", "and", "for", "with", "you", "our", "are", "this", "that", "will",
    "have", "from", "your", "who", "all", "can", "but", "not", "use", "using",
}


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def keywords(text: str) -> set[str]:
    """Content words minus stopwords; includes multiword skills found verbatim."""
    text_l = (text or "").lower()
    single = {t for t in tokenize(text) if t not in _STOPWORDS and len(t) > 2}
    multi = {s for s in SKILL_LEXICON if " " in s and s in text_l}
    return single | multi


def extract_skills(text: str) -> set[str]:
    """Skills present in text by matching against the curated lexicon.

    Handles common aliases (e.g. "nodejs" -> "node.js") so differently-worded
    requirements still register.
    """
    text_l = (text or "").lower()
    tokens = set(tokenize(text))
    found = set()
    for skill in SKILL_LEXICON:
        if " " in skill or "." in skill or "/" in skill or "+" in skill or "#" in skill:
            if skill in text_l:
                found.add(skill)
        elif skill in tokens:
            found.add(skill)
    for alias, canonical in _SKILL_ALIASES.items():
        if alias in text_l:
            found.add(canonical)
    return found


def normalize_skills(skills: Iterable[str]) -> set[str]:
    """Lower-case, strip, and canonicalise a list of skill strings."""
    out = set()
    for raw in skills or []:
        s = str(raw).strip().lower()
        if not s:
            continue
        out.add(_SKILL_ALIASES.get(s, s))
    return out


def coverage(have: Iterable[str], required: Iterable[str]) -> float:
    """Fraction of ``required`` items present in ``have`` (0..1).

    This is the right metric for ATS skill match: it measures how many of the
    job's requirements the candidate satisfies, regardless of how many extra
    skills the candidate lists (unlike Jaccard, which penalises breadth).
    """
    required = set(required)
    if not required:
        return 0.0
    have = set(have)
    return len(have & required) / len(required)


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    a, b = set(a), set(b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cosine(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(x * y for x, y in zip(vec_a, vec_b))
    na = math.sqrt(sum(x * x for x in vec_a))
    nb = math.sqrt(sum(y * y for y in vec_b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def keyword_density(resume_text: str, job_text: str) -> float:
    """Fraction of job keywords that appear in the resume (0..1)."""
    job_kw = keywords(job_text)
    if not job_kw:
        return 0.0
    resume_kw = keywords(resume_text)
    return len(job_kw & resume_kw) / len(job_kw)


def term_frequencies(text: str) -> Counter:
    return Counter(tokenize(text))
