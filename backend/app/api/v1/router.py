"""Aggregate v1 API router."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    analysis,
    applications,
    auth,
    insights,
    jobs,
    resume,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(resume.router)
api_router.include_router(jobs.router)
api_router.include_router(analysis.router)
api_router.include_router(applications.router)
api_router.include_router(insights.router)
