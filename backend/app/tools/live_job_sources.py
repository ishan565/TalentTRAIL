"""Live job providers — real, latest postings from public job APIs.

These adapters call real job APIs and normalise their responses into the same
``JobPostingDTO`` shape used by the mock providers, so the Job Discovery Agent
needs zero changes.

Sources:
- Google Jobs (via SerpApi) — real Google "for Jobs" results with FULL job
  descriptions, location-aware (e.g. India). Used first when ``SERPAPI_KEY`` is
  set; everything else acts as a free, key-less fallback.
- Remotive   (https://remotive.com/api/remote-jobs)      — remote tech jobs
- Arbeitnow  (https://www.arbeitnow.com/api/job-board-api) — EU + remote jobs
- Jobicy     (https://jobicy.com/api/v2/remote-jobs)       — remote jobs, incl. internships

All requests are best-effort: any network/parse error yields an empty list so a
single failing source never breaks discovery. Internship detection is based on
title/level keywords so the copilot can surface internships alongside jobs.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from html import unescape

import httpx
import structlog

from app.core.config import settings
from app.db.models import JobSource

log = structlog.get_logger(__name__)

_INTERNSHIP_RE = re.compile(r"\b(intern|internship|trainee|co-?op|apprentice)\b", re.I)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str | None) -> str:
    if not text:
        return ""
    return unescape(_TAG_RE.sub(" ", text)).strip()


def _is_internship(title: str, level: str = "") -> bool:
    return bool(_INTERNSHIP_RE.search(f"{title} {level}"))


def _parse_date(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:19], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def _client() -> httpx.Client:
    return httpx.Client(
        timeout=settings.JOB_API_TIMEOUT,
        verify=settings.JOB_API_VERIFY_SSL,
        follow_redirects=True,
        headers={"User-Agent": "TalentTrail/1.0"},
    )


def _matches(query: str, *fields: str) -> bool:
    """Loose keyword match: any query token present in any field."""
    if not query:
        return True
    haystack = " ".join(f.lower() for f in fields if f)
    tokens = [t for t in re.split(r"\W+", query.lower()) if len(t) > 1]
    return any(t in haystack for t in tokens)


# --------------------------------------------------------------------------- #
# Remotive
# --------------------------------------------------------------------------- #
def fetch_remotive(query: str, limit: int) -> list[dict]:
    with _client() as c:
        r = c.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": query or "developer", "limit": limit},
        )
        r.raise_for_status()
        jobs = r.json().get("jobs", [])

    out: list[dict] = []
    for j in jobs[:limit]:
        title = j.get("title", "")
        out.append(
            {
                "external_id": f"remotive-{j.get('id')}",
                "source": JobSource.REMOTIVE,
                "title": title,
                "company": j.get("company_name", "Unknown"),
                "location": j.get("candidate_required_location") or "Remote",
                "url": j.get("url", ""),
                "description": _strip_html(j.get("description"))[:2000],
                "skills": [t.strip().lower() for t in (j.get("tags") or [])][:12],
                "salary": j.get("salary") or None,
                "job_type": j.get("job_type") or None,
                "is_internship": _is_internship(title, j.get("job_type", "")),
                "posted_at": _parse_date(j.get("publication_date")),
            }
        )
    return out


# --------------------------------------------------------------------------- #
# Arbeitnow
# --------------------------------------------------------------------------- #
def fetch_arbeitnow(query: str, limit: int) -> list[dict]:
    with _client() as c:
        r = c.get("https://www.arbeitnow.com/api/job-board-api")
        r.raise_for_status()
        jobs = r.json().get("data", [])

    out: list[dict] = []
    for j in jobs:
        title = j.get("title", "")
        tags = [t.strip().lower() for t in (j.get("tags") or [])]
        if not _matches(query, title, j.get("description", ""), " ".join(tags)):
            continue
        out.append(
            {
                "external_id": f"arbeitnow-{j.get('slug')}",
                "source": JobSource.ARBEITNOW,
                "title": title,
                "company": j.get("company_name", "Unknown"),
                "location": j.get("location") or ("Remote" if j.get("remote") else ""),
                "url": j.get("url", ""),
                "description": _strip_html(j.get("description"))[:2000],
                "skills": tags[:12],
                "salary": None,
                "job_type": ", ".join(j.get("job_types") or []) or None,
                "is_internship": _is_internship(title, " ".join(j.get("job_types") or [])),
                "posted_at": _parse_date(
                    datetime.fromtimestamp(
                        j.get("created_at", 0), tz=timezone.utc
                    ).isoformat()
                    if isinstance(j.get("created_at"), (int, float))
                    else None
                ),
            }
        )
        if len(out) >= limit:
            break
    return out


# --------------------------------------------------------------------------- #
# Jobicy
# --------------------------------------------------------------------------- #
def fetch_jobicy(query: str, limit: int) -> list[dict]:
    params = {"count": min(limit, 50)}
    if query:
        params["tag"] = query
    with _client() as c:
        r = c.get("https://jobicy.com/api/v2/remote-jobs", params=params)
        r.raise_for_status()
        jobs = r.json().get("jobs", [])

    out: list[dict] = []
    for j in jobs[:limit]:
        title = j.get("jobTitle", "")
        level = j.get("jobLevel", "") or ""
        industries = j.get("jobIndustry") or []
        out.append(
            {
                "external_id": f"jobicy-{j.get('id')}",
                "source": JobSource.JOBICY,
                "title": title,
                "company": j.get("companyName", "Unknown"),
                "location": j.get("jobGeo") or "Remote",
                "url": j.get("url", ""),
                "description": _strip_html(
                    j.get("jobDescription") or j.get("jobExcerpt")
                )[:2000],
                "skills": [i.strip().lower() for i in industries][:12],
                "salary": None,
                "job_type": ", ".join(j.get("jobType") or []) or None,
                "is_internship": _is_internship(title, level),
                "posted_at": _parse_date(j.get("pubDate")),
            }
        )
    return out


# Order matters: most relevant/largest first.
LIVE_FETCHERS = (fetch_remotive, fetch_jobicy, fetch_arbeitnow)


# --------------------------------------------------------------------------- #
# Google Jobs (via SerpApi)
# --------------------------------------------------------------------------- #
def _parse_relative_date(value: str | None) -> datetime:
    """Convert SerpApi's relative 'posted_at' (e.g. '3 days ago') to a datetime."""
    now = datetime.now(timezone.utc)
    if not value:
        return now
    m = re.search(r"(\d+)\s*(hour|day|week|month)", value.lower())
    if not m:
        return now
    n = int(m.group(1))
    unit = m.group(2)
    days = {"hour": n / 24, "day": n, "week": n * 7, "month": n * 30}.get(unit, 0)
    from datetime import timedelta

    return now - timedelta(days=days)


def fetch_google_jobs(query: str, limit: int, location: str | None = None) -> list[dict]:
    """Fetch real Google Jobs results (with full JDs) via the SerpApi engine.

    Requires ``settings.SERPAPI_KEY``. Returns postings normalised to the same
    DTO shape as the other providers. Raises on hard failure so the caller can
    fall back to the free public APIs.
    """
    if not settings.SERPAPI_KEY:
        raise RuntimeError("SERPAPI_KEY not configured")

    loc = location or settings.DEFAULT_JOB_LOCATION or "India"
    params = {
        "engine": "google_jobs",
        "q": query or "software engineer",
        "location": loc,
        "hl": "en",
        "gl": "in" if "india" in loc.lower() else "us",
        "api_key": settings.SERPAPI_KEY,
    }
    with _client() as c:
        r = c.get("https://serpapi.com/search.json", params=params)
        r.raise_for_status()
        payload = r.json()

    if payload.get("error"):
        raise RuntimeError(f"serpapi: {payload['error']}")

    results = payload.get("jobs_results", []) or []
    out: list[dict] = []
    for j in results[:limit]:
        title = j.get("title", "")
        ext = j.get("detected_extensions") or {}
        schedule = ext.get("schedule_type") or ""
        # Prefer a real apply link when available.
        apply_options = j.get("apply_options") or []
        url = (apply_options[0].get("link") if apply_options else "") or j.get(
            "share_link", ""
        )
        # SerpApi returns the FULL job description already — no extra fetch needed.
        description = _strip_html(j.get("description"))[:4000]
        highlights = j.get("job_highlights") or []
        skills: list[str] = []
        for block in highlights:
            for item in block.get("items", []) or []:
                skills.append(item.strip().lower())
        out.append(
            {
                "external_id": f"google-{j.get('job_id') or abs(hash(title + (j.get('company_name') or '')))}",
                "source": JobSource.GOOGLE_JOBS,
                "title": title,
                "company": j.get("company_name", "Unknown"),
                "location": j.get("location") or loc,
                "url": url,
                "description": description,
                "skills": skills[:12],
                "salary": ext.get("salary") or None,
                "job_type": schedule or None,
                "is_internship": _is_internship(title, schedule),
                "posted_at": _parse_relative_date(ext.get("posted_at")),
            }
        )
    return out


class AllSourcesFailed(RuntimeError):
    """Raised when every live provider errored (network down / blocked)."""


def fetch_live(
    query: str, location: str | None = None, limit: int = 30, internships: bool = False
) -> list[dict]:
    """Fetch live postings, preferring Google Jobs (SerpApi) when configured.

    Strategy:
    1. If a SerpApi key is set, try Google Jobs first (real JDs, India-aware).
       On success we use those results directly.
    2. Otherwise (or if SerpApi fails) fan out to the free public APIs and
       apply a best-effort location filter.

    Raises ``AllSourcesFailed`` if *every* available provider errored, so the
    caller can fall back to mock data. An empty result from a healthy provider
    is returned as-is — never masked with fake postings.
    """
    effective_location = location or settings.DEFAULT_JOB_LOCATION or None

    # 1) Preferred path: Google Jobs via SerpApi (full JDs, location-aware).
    if settings.SERPAPI_KEY:
        try:
            google = fetch_google_jobs(query, limit, effective_location)
            if internships:
                google = [j for j in google if j.get("is_internship")]
            if google:
                return google[:limit]
            log.info("jobsource.google.empty", query=query, location=effective_location)
        except Exception as exc:  # noqa: BLE001
            log.warning("jobsource.google.fail", error=str(exc))

    # 2) Fallback path: free public APIs.
    per_source = max(5, limit // len(LIVE_FETCHERS) + 3)
    collected: list[dict] = []
    failures = 0

    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=len(LIVE_FETCHERS)) as pool:
        futures = {pool.submit(f, query, per_source): f for f in LIVE_FETCHERS}
        for fut in as_completed(futures):
            f = futures[fut]
            try:
                collected.extend(fut.result())
            except Exception as exc:  # noqa: BLE001
                failures += 1
                log.warning("jobsource.live.fail", source=f.__name__, error=str(exc))

    if failures == len(LIVE_FETCHERS):
        raise AllSourcesFailed("all live job providers failed")

    # Optional location filter (best-effort substring match). Remote/worldwide
    # postings are always kept since they're open to candidates in any country.
    # The free boards are global/remote-first, so a strict location match can be
    # very thin — if it is, we keep the broader remote set so the page isn't
    # empty (SerpApi above is the accurate location-specific path).
    if effective_location:
        loc = effective_location.lower()
        located = [
            j
            for j in collected
            if loc in (j.get("location") or "").lower()
            or "remote" in (j.get("location") or "").lower()
            or "worldwide" in (j.get("location") or "").lower()
            or "anywhere" in (j.get("location") or "").lower()
        ]
        if len(located) >= 5:
            collected = located

    if internships:
        collected = [j for j in collected if j.get("is_internship")]

    return collected[:limit]
