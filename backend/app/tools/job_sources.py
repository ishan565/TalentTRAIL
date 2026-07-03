"""Job source abstraction layer.

Defines a common ``JobProvider`` interface so LinkedIn / Greenhouse / Lever /
Ashby / Wellfound / company pages all expose the same ``search()`` contract.
The Job Discovery Agent depends only on this interface (Dependency Inversion),
so adding a real ATS integration later means writing one adapter — no agent
changes.

The bundled providers return realistic *mock* postings so the whole pipeline
runs offline without scraping (which would violate most sites' ToS). Swap the
body of ``search`` with a real API/ingestion call to go live.
"""
from __future__ import annotations

import abc
from datetime import datetime, timedelta, timezone
from typing import Iterable

from app.db.models import JobSource


class JobPostingDTO(dict):
    """Plain dict DTO (title, company, location, url, description, skills, ...)."""


class JobProvider(abc.ABC):
    source: JobSource

    @abc.abstractmethod
    def search(self, query: str, location: str | None = None, limit: int = 20) -> list[dict]:
        ...


class _MockProvider(JobProvider):
    """Deterministic provider that synthesises plausible postings from a query."""

    def __init__(self, source: JobSource, companies: list[str]):
        self.source = source
        self._companies = companies

    def search(self, query: str, location: str | None = None, limit: int = 20) -> list[dict]:
        now = datetime.now(timezone.utc)
        roles = [query, f"Senior {query}", f"Junior {query}"]
        skills_pool = ["python", "fastapi", "docker", "aws", "react", "langchain", "postgresql"]
        out: list[dict] = []
        for i in range(min(limit, len(self._companies) * len(roles))):
            company = self._companies[i % len(self._companies)]
            role = roles[i % len(roles)]
            out.append(
                JobPostingDTO(
                    external_id=f"{self.source.value}-{abs(hash((company, role))) % 10_000}",
                    source=self.source,
                    title=role,
                    company=company,
                    location=location or "Remote",
                    url=f"https://{self.source.value}.example.com/jobs/{i}",
                    description=(
                        f"{company} is hiring a {role}. Required skills: "
                        f"{', '.join(skills_pool[: 3 + (i % 4)])}. "
                        "Experience building scalable backend services."
                    ),
                    skills=skills_pool[: 3 + (i % 4)],
                    posted_at=now - timedelta(days=i % 21),
                )
            )
        return out


# Registry of available providers, keyed by source.
PROVIDERS: dict[JobSource, JobProvider] = {
    JobSource.GREENHOUSE: _MockProvider(JobSource.GREENHOUSE, ["Acme AI", "Nimbus", "Forge"]),
    JobSource.LEVER: _MockProvider(JobSource.LEVER, ["DeepHire", "Quanta", "Cobalt"]),
    JobSource.ASHBY: _MockProvider(JobSource.ASHBY, ["Vector Labs", "Helix"]),
    JobSource.WELLFOUND: _MockProvider(JobSource.WELLFOUND, ["SeedAI", "LaunchPad"]),
    JobSource.LINKEDIN: _MockProvider(JobSource.LINKEDIN, ["BigCo", "Globex"]),
    JobSource.CAREER_PAGE: _MockProvider(JobSource.CAREER_PAGE, ["Stripe", "Datadog"]),
}


def aggregate(
    query: str,
    location: str | None = None,
    sources: Iterable[JobSource] | None = None,
    limit: int = 20,
    internships: bool = False,
) -> list[dict]:
    """Fan out to job providers, then deduplicate by external_id/title+company.

    When ``settings.USE_LIVE_JOBS`` is enabled, real postings are fetched from
    public job APIs (Remotive, Jobicy, Arbeitnow). If live fetching is disabled
    or returns nothing (offline/tests), it falls back to deterministic mock
    providers so the pipeline always produces results.
    """
    from app.core.config import settings  # local import avoids cycles

    collected: list[dict] = []
    live_attempted = False

    if settings.USE_LIVE_JOBS:
        try:
            from app.tools import live_job_sources

            collected = live_job_sources.fetch_live(
                query=query,
                location=location,
                limit=limit,
                internships=internships,
            )
            live_attempted = True
        except Exception:  # noqa: BLE001 — all providers down: fall back to mock
            live_attempted = False

    # Fall back to mock providers only when live is disabled or the network
    # failed entirely. A healthy-but-empty live result is returned as-is so we
    # never show fabricated postings.
    if not live_attempted and not collected:
        chosen = list(sources) if sources else list(PROVIDERS.keys())
        per_source = max(1, limit // max(1, len(chosen)))
        for src in chosen:
            provider = PROVIDERS.get(src)
            if provider:
                collected.extend(provider.search(query, location, per_source))

    seen: set = set()
    deduped: list[dict] = []
    for job in collected:
        key = job.get("external_id") or (job["title"], job["company"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(job)
    return deduped[:limit]
