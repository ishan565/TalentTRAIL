"""Create tables and seed a demo user/jobs for first-run experience."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.logging import get_logger
from app.core.security import hash_password
from app.db import models
from app.db.session import Base, SessionLocal, engine

logger = get_logger(__name__)


def init_db() -> None:
    # ``import models`` above registers every table on Base.metadata.
    Base.metadata.create_all(bind=engine)
    _seed()
    logger.info("db.init.complete")


def _seed() -> None:
    db = SessionLocal()
    try:
        if db.query(models.User).first():
            return  # already seeded

        demo = models.User(
            email="demo@talenttrail.dev",
            full_name="Demo User",
            hashed_password=hash_password("demo1234"),
        )
        db.add(demo)
        db.flush()

        now = datetime.now(timezone.utc)
        sample_jobs = [
            models.JobPosting(
                external_id="gh-1",
                source=models.JobSource.GREENHOUSE,
                title="Backend Engineer (Python)",
                company="Acme AI",
                location="Remote",
                url="https://example.com/jobs/1",
                description=(
                    "We are looking for a Python backend engineer with FastAPI, "
                    "PostgreSQL, Docker, and experience building LLM-powered apps "
                    "with LangChain. Bonus: AWS, Kubernetes, vector databases."
                ),
                skills=["python", "fastapi", "postgresql", "docker", "langchain"],
                posted_at=now - timedelta(days=2),
            ),
            models.JobPosting(
                external_id="lv-2",
                source=models.JobSource.LEVER,
                title="Machine Learning Engineer",
                company="DeepHire",
                location="San Francisco, CA",
                url="https://example.com/jobs/2",
                description=(
                    "ML engineer to build recommendation systems. Required: Python, "
                    "PyTorch, embeddings, ChromaDB, semantic search, MLOps."
                ),
                skills=["python", "pytorch", "embeddings", "chromadb", "mlops"],
                posted_at=now - timedelta(days=10),
            ),
        ]
        db.add_all(sample_jobs)
        db.commit()
        logger.info("db.seed.complete", demo_email=demo.email)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
