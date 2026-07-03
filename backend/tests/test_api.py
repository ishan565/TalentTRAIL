"""API integration tests (auth, resume, jobs, applications, analytics)."""
from __future__ import annotations


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_login(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "a@b.dev", "password": "password123", "full_name": "AB"},
    )
    assert r.status_code == 201
    r2 = client.post(
        "/api/v1/auth/login", data={"username": "a@b.dev", "password": "password123"}
    )
    assert r2.status_code == 200
    assert "access_token" in r2.json()


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_resume_upload_and_jobs_flow(client, auth_headers):
    # Upload a tiny text resume.
    files = {"file": ("resume.txt", b"Python FastAPI Docker engineer with PostgreSQL.", "text/plain")}
    up = client.post("/api/v1/resume/upload", files=files, headers=auth_headers)
    assert up.status_code == 200
    resume_id = up.json()["id"]

    an = client.post(f"/api/v1/resume/{resume_id}/analyze", headers=auth_headers)
    assert an.status_code == 200
    assert "python" in (an.json()["parsed"]["skills"])

    search = client.get("/api/v1/jobs/search", params={"query": "Python Engineer"}, headers=auth_headers)
    assert search.status_code == 200
    results = search.json()["results"]
    assert len(results) > 0
    job_id = results[0]["job"]["id"]

    ats = client.post(
        "/api/v1/ats/score", json={"resume_id": resume_id, "job_id": job_id}, headers=auth_headers
    )
    assert ats.status_code == 200
    assert 0 <= ats.json()["total_score"] <= 100


def test_application_board(client, auth_headers):
    files = {"file": ("r.txt", b"Python engineer", "text/plain")}
    client.post("/api/v1/resume/upload", files=files, headers=auth_headers)
    search = client.get("/api/v1/jobs/search", params={"query": "Python"}, headers=auth_headers)
    job_id = search.json()["results"][0]["job"]["id"]

    created = client.post(
        "/api/v1/applications", json={"job_id": job_id, "status": "applied"}, headers=auth_headers
    )
    assert created.status_code == 201
    app_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/applications/{app_id}", json={"status": "interview"}, headers=auth_headers
    )
    assert updated.json()["status"] == "interview"

    analytics = client.get("/api/v1/analytics", headers=auth_headers)
    assert analytics.status_code == 200
    assert analytics.json()["total_applications"] >= 1
