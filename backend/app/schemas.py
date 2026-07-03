"""Pydantic v2 schemas (API request/response contracts).

These are the *boundary* types: they validate untrusted input and shape
serialized output. ORM models stay internal; schemas are what the API speaks.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.models import ApplicationStatus, JobSource


# ----- shared -----
class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ----- auth -----
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ----- resume -----
class ResumeOut(ORMModel):
    id: int
    version: int
    is_active: bool
    filename: Optional[str]
    summary: Optional[str]
    parsed: Optional[dict]
    created_at: datetime


class SkillOut(ORMModel):
    id: int
    name: str
    category: Optional[str]
    proficiency: Optional[str]


# ----- jobs -----
class JobOut(ORMModel):
    id: int
    source: JobSource
    title: str
    company: str
    location: Optional[str]
    url: Optional[str]
    description: Optional[str]
    skills: Optional[List[str]]
    posted_at: Optional[datetime]


class JobSearchQuery(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    location: Optional[str] = None
    sources: Optional[List[JobSource]] = None
    limit: int = Field(default=20, ge=1, le=100)


class RankedJob(BaseModel):
    job: JobOut
    final_score: float
    keyword_score: float
    semantic_score: float
    ats_score: float
    recency_score: float
    explanation: dict[str, Any]


# ----- ATS -----
class ATSRequest(BaseModel):
    resume_id: int
    job_id: int


class ATSResult(BaseModel):
    total_score: float
    skills_match: float
    projects_match: float
    experience_match: float
    education_match: float
    keyword_density: float
    breakdown: dict[str, Any]


# ----- keywords -----
class KeywordRequest(BaseModel):
    resume_id: int
    job_id: int


class KeywordResult(BaseModel):
    present: List[str]
    missing: dict[str, List[str]]  # categorised: skills/technologies/frameworks/tools


# ----- optimize -----
class OptimizeRequest(BaseModel):
    resume_id: int
    job_id: int


class OptimizeResult(BaseModel):
    optimized_bullets: List[str]
    improved_summary: str
    notes: List[str]


# ----- cover letter -----
class CoverLetterRequest(BaseModel):
    resume_id: int
    job_id: int
    company_type: str = Field(default="startup")  # startup/faang/enterprise/ai
    tone: str = Field(default="professional")


class CoverLetterResult(BaseModel):
    content: str


# ----- applications -----
class ApplicationCreate(BaseModel):
    job_id: int
    status: ApplicationStatus = ApplicationStatus.SAVED
    notes: Optional[str] = None


class ManualApplicationCreate(BaseModel):
    """Add a job to the tracker by typing its details (no prior job posting)."""

    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    location: Optional[str] = Field(default=None, max_length=255)
    url: Optional[str] = Field(default=None, max_length=1024)
    status: ApplicationStatus = ApplicationStatus.SAVED
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None


class ApplicationOut(ORMModel):
    id: int
    job_id: int
    status: ApplicationStatus
    notes: Optional[str]
    applied_at: Optional[datetime]
    created_at: datetime
    job: Optional[JobOut] = None


# ----- analytics -----
class AnalyticsOut(BaseModel):
    total_applications: int
    by_status: dict[str, int]
    interview_rate: float
    offer_rate: float
    applications_over_time: List[dict[str, Any]]
    top_matched_skills: List[dict[str, Any]]
    missing_skills: List[dict[str, Any]]
    source_performance: List[dict[str, Any]]


# ----- career roadmap -----
class RoadmapResult(BaseModel):
    target_roles: List[str]
    skills_to_learn: List[str]
    projects_to_build: List[str]
    certifications: List[str]
    roadmap: dict[str, Any]
