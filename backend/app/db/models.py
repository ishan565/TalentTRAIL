"""ORM models for TalentTrail.

A single module keeps relationships easy to read for a portfolio project. In a
larger codebase these would be split per-aggregate. Design notes:

* Every table has an integer surrogate PK + ``created_at``/``updated_at``.
* JSON columns store semi-structured agent output (skills, parsed resume,
  keyword analysis) so the schema stays stable while LLM output evolves.
* Indexes are added on every foreign key and on common filter columns
  (``user_id``, ``status``, ``match_score``) for fast dashboard queries.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class ApplicationStatus(str, enum.Enum):
    SAVED = "saved"
    APPLIED = "applied"
    OA = "oa"
    INTERVIEW = "interview"
    FINAL_ROUND = "final_round"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class JobSource(str, enum.Enum):
    LINKEDIN = "linkedin"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    WELLFOUND = "wellfound"
    CAREER_PAGE = "career_page"
    MANUAL = "manual"
    # Live public job APIs
    REMOTIVE = "remotive"
    ARBEITNOW = "arbeitnow"
    JOBICY = "jobicy"
    GOOGLE_JOBS = "google_jobs"


# --------------------------------------------------------------------------- #
# Core tables
# --------------------------------------------------------------------------- #
class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    oauth_provider: Mapped[str | None] = mapped_column(String(50))  # e.g. "google"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    resumes: Mapped[list["Resume"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    recommendations: Mapped[list["CareerRecommendation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Resume(TimestampMixin, Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)  # resume version history
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    filename: Mapped[str | None] = mapped_column(String(512))
    raw_text: Mapped[str | None] = mapped_column(Text)
    # Structured Resume JSON produced by the Resume Analysis Agent.
    parsed: Mapped[dict | None] = mapped_column(JSON)
    summary: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="resumes")
    skills: Mapped[list["Skill"]] = relationship(back_populates="resume", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship(back_populates="resume", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str | None] = mapped_column(String(80))  # language/framework/tool/...
    proficiency: Mapped[str | None] = mapped_column(String(40))

    resume: Mapped[Resume] = relationship(back_populates="skills")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    tech_stack: Mapped[list | None] = mapped_column(JSON)

    resume: Mapped[Resume] = relationship(back_populates="projects")


class JobPosting(TimestampMixin, Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)  # dedup key
    source: Mapped[JobSource] = mapped_column(Enum(JobSource), default=JobSource.MANUAL, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    company: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(1024))
    description: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[list | None] = mapped_column(JSON)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    matches: Mapped[list["JobMatch"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class JobMatch(TimestampMixin, Base):
    __tablename__ = "job_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id", ondelete="CASCADE"), index=True)

    keyword_score: Mapped[float] = mapped_column(Float, default=0.0)
    semantic_score: Mapped[float] = mapped_column(Float, default=0.0)
    ats_score: Mapped[float] = mapped_column(Float, default=0.0)
    recency_score: Mapped[float] = mapped_column(Float, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    explanation: Mapped[dict | None] = mapped_column(JSON)

    job: Mapped[JobPosting] = relationship(back_populates="matches")


class ATSScore(TimestampMixin, Base):
    __tablename__ = "ats_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("job_postings.id", ondelete="SET NULL"), index=True)

    skills_match: Mapped[float] = mapped_column(Float, default=0.0)
    projects_match: Mapped[float] = mapped_column(Float, default=0.0)
    experience_match: Mapped[float] = mapped_column(Float, default=0.0)
    education_match: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_density: Mapped[float] = mapped_column(Float, default=0.0)
    total_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    breakdown: Mapped[dict | None] = mapped_column(JSON)


class KeywordAnalysis(TimestampMixin, Base):
    __tablename__ = "keyword_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("job_postings.id", ondelete="SET NULL"), index=True)
    missing: Mapped[dict | None] = mapped_column(JSON)   # categorised missing keywords
    present: Mapped[list | None] = mapped_column(JSON)


class Application(TimestampMixin, Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id", ondelete="CASCADE"), index=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.SAVED, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="applications")
    job: Mapped[JobPosting] = relationship()


class CoverLetter(TimestampMixin, Base):
    __tablename__ = "cover_letters"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("job_postings.id", ondelete="SET NULL"), index=True)
    company_type: Mapped[str | None] = mapped_column(String(40))  # startup/faang/enterprise/ai
    content: Mapped[str] = mapped_column(Text)


class CareerRecommendation(TimestampMixin, Base):
    __tablename__ = "career_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_roles: Mapped[list | None] = mapped_column(JSON)
    skills_to_learn: Mapped[list | None] = mapped_column(JSON)
    projects_to_build: Mapped[list | None] = mapped_column(JSON)
    certifications: Mapped[list | None] = mapped_column(JSON)
    roadmap: Mapped[dict | None] = mapped_column(JSON)

    user: Mapped[User] = relationship(back_populates="recommendations")


class AgentRun(TimestampMixin, Base):
    """Observability: one row per LangGraph execution for replay/debugging."""

    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    graph: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(40), default="running")
    input_summary: Mapped[dict | None] = mapped_column(JSON)
    execution_history: Mapped[list | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    detail: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(64))
