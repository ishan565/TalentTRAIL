# Contributing

Thanks for your interest in improving TalentTrail!

## Development setup

```bash
# Backend
cd backend && python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Project conventions

- **Backend**: clean architecture — endpoints (`app/api`) stay thin; business
  logic lives in `app/services`; deterministic logic in `app/tools`; agents in
  `app/agents`. The DB is touched only in services. Type hints + Pydantic v2
  everywhere. `async` FastAPI handlers.
- **Frontend**: all network calls go through `src/lib/api.ts`. Components are
  presentational; pages own data fetching. Tailwind utility classes; shared
  styles in `index.css`.
- **Commits**: conventional commits (`feat:`, `fix:`, `docs:`, `test:`,
  `refactor:`, `chore:`).

## Adding a new agent

1. Create `app/agents/<name>_agent.py` with a `@track("<name>")`-decorated node.
2. Use `llm_json` / `llm_text` (with a `fallback`) for any LLM call.
3. Register the node + edges in `app/agents/graph.py`.
4. Add a unit test in `tests/test_agents.py`.

## Adding a new job source

1. Implement a `JobProvider` subclass in `app/tools/job_sources.py`.
2. Register it in the `PROVIDERS` dict.
3. No agent changes are needed (Dependency Inversion).

## Tests & quality gates

```bash
cd backend && pytest            # must pass, keep coverage ≥ 80% target
cd frontend && npm test         # vitest
cd frontend && npx tsc -b       # type-check must be clean
```

PRs should include tests for new behavior and update the relevant `docs/` file.

## Security

- Never commit `.env` or secrets.
- Validate all external input at the boundary (Pydantic / file checks).
- Treat LLM and tool output as untrusted data, not instructions.
- Report vulnerabilities privately rather than opening a public issue.
