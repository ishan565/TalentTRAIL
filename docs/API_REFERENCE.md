# API Reference

Base URL: `http://localhost:8000/api/v1`
Interactive docs (OpenAPI): `http://localhost:8000/docs`

All protected endpoints require `Authorization: Bearer <access_token>`.

## Auth

| Method | Path | Body | Description |
| --- | --- | --- | --- |
| POST | `/auth/register` | `{email, password, full_name?}` | Create account |
| POST | `/auth/login` | form: `username`, `password` | Returns access + refresh tokens |
| POST | `/auth/refresh` | `refresh_token` (query) | New token pair |
| GET | `/auth/me` | — | Current user |

```bash
# Login (note: OAuth2 form uses `username` for the email)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=demo@talenttrail.dev&password=demo1234"
```

## Resume

| Method | Path | Description |
| --- | --- | --- |
| POST | `/resume/upload` | multipart `file` (PDF/DOCX/TXT) → new resume version |
| POST | `/resume/{id}/analyze` | Run Resume Analysis Agent → structured JSON |
| GET | `/resume` | List resume versions |
| GET | `/resume/active` | Active resume |

## Jobs

| Method | Path | Query | Description |
| --- | --- | --- | --- |
| GET | `/jobs/search` | `query`, `location?`, `limit?` | Aggregate + rank against active resume |
| GET | `/jobs/recommendations` | `limit?` | Stored top matches |
| GET | `/jobs/{id}` | — | Single posting |

## Analysis

| Method | Path | Body | Description |
| --- | --- | --- | --- |
| POST | `/ats/score` | `{resume_id, job_id}` | Explainable ATS 0–100 |
| POST | `/keywords/analyze` | `{resume_id, job_id}` | Categorised missing keywords |
| POST | `/resume/optimize` | `{resume_id, job_id}` | ATS-optimized bullets + summary |
| POST | `/cover-letter/generate` | `{resume_id, job_id, company_type}` | Tailored cover letter |

## Applications

| Method | Path | Body | Description |
| --- | --- | --- | --- |
| POST | `/applications` | `{job_id, status?, notes?}` | Create card |
| GET | `/applications` | — | List cards |
| PATCH | `/applications/{id}` | `{status?, notes?}` | Move/update card |
| DELETE | `/applications/{id}` | — | Remove card |

## Insights

| Method | Path | Description |
| --- | --- | --- |
| GET | `/analytics` | Dashboard metrics (rates, time series, skills, sources) |
| GET | `/career-roadmap` | 30/60/90-day plan |
| POST | `/pipeline/run?query=…` | Execute the full LangGraph multi-agent pipeline |

## Example: end-to-end with curl

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -d "username=demo@talenttrail.dev&password=demo1234" | jq -r .access_token)

# Upload + analyze
RID=$(curl -s -X POST localhost:8000/api/v1/resume/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@resume.pdf" | jq .id)
curl -s -X POST localhost:8000/api/v1/resume/$RID/analyze -H "Authorization: Bearer $TOKEN"

# Search + score
JID=$(curl -s "localhost:8000/api/v1/jobs/search?query=Python%20Engineer" \
  -H "Authorization: Bearer $TOKEN" | jq '.results[0].job.id')
curl -s -X POST localhost:8000/api/v1/ats/score \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"resume_id\":$RID,\"job_id\":$JID}"
```

## Error format

```json
{ "detail": "Human-readable message" }
```

Standard codes: `400` validation, `401` unauthorized, `404` not found, `413`
payload too large, `429` rate limited.
