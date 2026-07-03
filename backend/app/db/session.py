"""SQLAlchemy engine and session factory.

Supports SQLite (dev) and PostgreSQL (prod) transparently. The
``check_same_thread`` flag is only needed for SQLite under FastAPI's threadpool.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


def get_db():
    """FastAPI dependency yielding a scoped session and guaranteeing cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
