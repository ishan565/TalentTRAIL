"""Pytest fixtures: isolated in-memory app + DB, no external services needed."""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_talenttrail.db")
# Force the deterministic hashing embedder (no network) by selecting azure with
# no embedding deployment. We set the vars explicitly (not just pop) so they
# override any value present in a developer's .env file, which pydantic-settings
# would otherwise read. Chat calls are wrapped in try/except with deterministic
# fallbacks, so no Azure traffic occurs during tests.
os.environ["LLM_PROVIDER"] = "azure"
os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"] = ""
os.environ["AZURE_OPENAI_API_KEY"] = ""
os.environ["AZURE_OPENAI_ENDPOINT"] = ""
os.environ.setdefault("SECRET_KEY", "test-secret-key-please-change")
# Use deterministic mock job providers in tests (no network / flakiness).
os.environ["USE_LIVE_JOBS"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def engine():
    # StaticPool + single shared connection so every session sees the same
    # in-memory database (otherwise each connection gets its own empty DB).
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture()
def db_session(engine):
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(engine):
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "t@test.dev", "password": "password123", "full_name": "T"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "t@test.dev", "password": "password123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
