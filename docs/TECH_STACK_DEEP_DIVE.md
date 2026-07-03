# 🧠 Technology Deep Dive — Every Tool, and *Why* It Was Chosen

> This document answers one question for **every** technology in the project: **"Why this, and not the alternatives?"** It covers frontend, backend, database, AI, and DevOps. For each choice you get: *what it is*, *the job it does here*, *what we considered instead*, and *why the alternative was rejected*.

If you only read one doc to sound competent in an interview about this project, read this one.

---

## Table of Contents
- [How to read this](#how-to-read-this)
- [Part 1 — Backend](#part-1--backend)
- [Part 2 — AI / LLM / Agents](#part-2--ai--llm--agents)
- [Part 3 — Database & persistence](#part-3--database--persistence)
- [Part 4 — Frontend](#part-4--frontend)
- [Part 5 — DevOps & infrastructure](#part-5--devops--infrastructure)
- [Part 6 — The "why" of the architecture itself](#part-6--the-why-of-the-architecture-itself)
- [One-page cheat sheet](#one-page-cheat-sheet)

---

## How to read this

Every entry follows the same template:

> **🔧 The tech** — one-line definition
> **Job here:** what it actually does in *this* codebase
> **Alternatives considered:** the real competitors
> **Why we chose this:** the deciding factors
> **Trade-offs we accepted:** nothing is free

---

## Part 1 — Backend

### 🔧 Python 3.12 — the backend language

**Job here:** Runs the entire backend — API, agents, scoring engines, DB access.

**Alternatives considered:** Node.js/TypeScript, Go, Java/Kotlin, Rust.

**Why we chose this:**
- **The AI ecosystem is Python-first.** LangGraph, LangChain, the OpenAI SDK, ChromaDB, NumPy, pypdf — all have Python as their primary, best-documented binding. Choosing anything else means fighting the ecosystem.
- **Readable for a portfolio.** Reviewers can skim the agents and immediately understand them.
- **3.12 specifically** for faster startup, better error messages, and mature typing (`X | None`, `Annotated`, `TypedDict`).

**Why not the alternatives:**
- **Node/TS:** great for the web layer, but the LLM-agent ecosystem (LangGraph especially) is far weaker. You'd be the second-class citizen.
- **Go/Rust:** superb performance, but this app is **I/O-bound** (waiting on the LLM and job APIs), not CPU-bound — so raw speed buys little, while you lose the AI libraries and write 3× the code.
- **Java:** verbose, and again the LLM tooling lags.

**Trade-off accepted:** Python is slower at raw CPU work. Irrelevant here because the bottleneck is network latency to the LLM, not Python.

---

### 🔧 FastAPI — the web framework

**Job here:** Defines every HTTP endpoint (`/auth/login`, `/ats/score`, `/pipeline/run`…), handles request validation, dependency injection, auth, and auto-generates interactive API docs at `/docs`.

**Alternatives considered:** Flask, Django (+ DRF), Express (Node), Starlette (raw).

**Why we chose this:**
- **Pydantic validation is built in.** You declare a request model (`ATSRequest`) and FastAPI validates the JSON, coerces types, and returns a clean 422 on bad input — *zero* manual checking.
- **Async-native.** `async def` endpoints + `httpx.AsyncClient` mean a slow LLM call doesn't block other requests. Critical when the pipeline can take 60–180 seconds.
- **Automatic OpenAPI docs.** `/docs` (Swagger) and `/redoc` are generated from your type hints — free, always-accurate API documentation.
- **Dependency injection** (`Depends(get_db)`, `Depends(get_current_user)`) makes auth and DB sessions composable and testable.

**Why not the alternatives:**
- **Flask:** synchronous by default; validation, docs, and DI are all bolt-on libraries you must wire yourself. More glue, less safety.
- **Django:** batteries-included but **heavyweight** — its ORM, admin, and templating are overkill for a JSON API, and its async story is still awkward. We don't need server-rendered HTML; React owns the UI.
- **Express:** would force the whole backend into Node, abandoning the Python AI ecosystem.

**Trade-off accepted:** FastAPI is younger than Flask/Django, so some niche extensions don't exist. We needed none of them.

---

### 🔧 Pydantic v2 + pydantic-settings — validation & configuration

**Job here:**
- **Pydantic** ([schemas.py](../backend/app/schemas.py)) defines the API's request/response shapes — the *contract* between frontend and backend.
- **pydantic-settings** ([config.py](../backend/app/core/config.py)) loads `.env` into one typed `Settings` object.

**Alternatives considered:** `dataclasses` + manual validation, `marshmallow`, `cerberus`, reading `os.environ` directly, `python-dotenv` alone.

**Why we chose this:**
- **One model = validation + serialization + docs.** A single `ATSResult` class validates output, serializes to JSON, *and* feeds the OpenAPI schema.
- **`from_attributes=True`** lets you return a SQLAlchemy ORM object straight from an endpoint and have it auto-serialized — no manual dict-building.
- **Typed config catches mistakes at startup**, not at 2 a.m. in production. `MAX_UPLOAD_MB: int` means a bad env value fails loudly and immediately.
- **v2 is written in Rust** under the hood → very fast validation.

**Why not the alternatives:**
- **Manual validation:** error-prone, repetitive, and you'd reinvent half of Pydantic.
- **marshmallow:** capable, but a separate schema layer disconnected from FastAPI's type hints — double the definitions.
- **Raw `os.environ`:** untyped, scattered, untestable. The whole point of `config.py` is that nothing else reads the environment directly.

**Trade-off accepted:** Pydantic v2 changed some APIs from v1; we pinned the version to avoid churn.

---

### 🔧 python-jose + passlib[bcrypt] — authentication

**Job here:** ([security.py](../backend/app/core/security.py)) `passlib`/`bcrypt` hash passwords; `python-jose` signs and verifies JWT access/refresh tokens.

**Alternatives considered:** `PyJWT` (instead of jose), `argon2` (instead of bcrypt), server-side sessions, a third-party auth provider (Auth0/Clerk/Firebase).

**Why we chose this:**
- **bcrypt** is the boring, battle-tested password hash: slow by design (resists brute force), salted automatically, universally trusted.
- **JWT** gives **stateless auth** — the signed token *is* the proof of identity, so the API needs no session store. This scales horizontally (any server can validate any token) and keeps the architecture simple.
- **jose** supports the full JWS/JWE spec if we later need encrypted tokens.

**Why not the alternatives:**
- **Server-side sessions:** require a shared session store (Redis/DB) and sticky routing — unnecessary complexity for a stateless API.
- **Auth0/Clerk:** great products, but add an external dependency, cost, and network hop for what is a learning/portfolio project. Rolling minimal JWT auth *demonstrates understanding*.
- **argon2:** arguably stronger than bcrypt, but bcrypt is more universally available and perfectly adequate here.

**Trade-off accepted:** JWTs can't be revoked before expiry without a denylist. Mitigated by short (60 min) access-token lifetimes + refresh tokens.

---

### 🔧 slowapi — rate limiting

**Job here:** ([main.py](../backend/app/main.py)) Caps each client IP at `120/minute` to prevent abuse and runaway LLM costs.

**Alternatives considered:** nginx rate limiting, a custom middleware, `fastapi-limiter` (Redis-based).

**Why we chose this:**
- **Zero infrastructure.** slowapi works in-process with no Redis required — ideal for a single-node deployment.
- **Per-route tuning.** You can decorate expensive endpoints (like `/pipeline/run`) with stricter limits.

**Why not the alternatives:**
- **fastapi-limiter:** needs Redis — more moving parts than this project warrants.
- **nginx-only:** works for coarse limits but can't express "this user, this endpoint" application logic.

**Trade-off accepted:** In-process counters reset on restart and aren't shared across multiple backend replicas. Fine for one node; swap to Redis when scaling out.

---

### 🔧 structlog — logging

**Job here:** ([logging.py](../backend/app/core/logging.py)) Emits **structured** logs — pretty & colored in dev, JSON in production.

**Alternatives considered:** stdlib `logging` alone, `loguru`, `print()`.

**Why we chose this:**
- **Structured key-value logs.** `logger.info("agent.done", agent="ats_scoring", ms=42)` becomes a JSON object a log aggregator (CloudWatch, Datadog) can filter and chart. Plain strings can't.
- **Dev vs prod rendering** from one config: humans get colors, machines get JSON.
- **Context binding** (`contextvars`) lets you attach a request id once and have it appear on every log line.

**Why not the alternatives:**
- **stdlib logging:** powerful but verbose to configure for structured output; structlog wraps it cleanly.
- **loguru:** lovely DX, but weaker structured/JSON story for production aggregation.
- **print():** no levels, no structure, no timestamps — untenable beyond a toy.

**Trade-off accepted:** One more dependency and a small learning curve over `print`.

---

### 🔧 httpx — HTTP client

**Job here:** Calls external **job APIs** ([live_job_sources.py](../backend/app/tools/live_job_sources.py)) and is the transport for the **Azure OpenAI SDK** ([llm.py](../backend/app/core/llm.py)).

**Alternatives considered:** `requests`, `aiohttp`, `urllib`.

**Why we chose this:**
- **Sync *and* async in one library** with the same API — matches FastAPI's async model.
- **Custom SSL control.** We build the httpx client ourselves so we can set `verify=False` behind a corporate SSL-intercepting proxy (the cause of many historical bugs). The OpenAI SDK accepts our pre-built client, so this control propagates to LLM calls too.
- **Connection pooling** via cached clients.

**Why not the alternatives:**
- **requests:** synchronous only, no native async — would block the event loop.
- **aiohttp:** async only, so you'd need a second library for sync code paths.

**Trade-off accepted:** httpx is slightly newer than requests; its maturity is now well proven.

---

### 🔧 pypdf + python-docx — document parsing

**Job here:** ([document_parser.py](../backend/app/tools/document_parser.py)) Extract raw text from uploaded **PDF** and **DOCX** resumes before the LLM structures it.

**Alternatives considered:** `PyMuPDF` (fitz), `pdfplumber`, `pdfminer.six`, `textract`, cloud OCR (AWS Textract).

**Why we chose this:**
- **Pure-Python, no system dependencies.** pypdf and python-docx install cleanly in a slim Docker image with no `apt-get` of native libraries — keeps the image small and the build reproducible.
- **Good enough for text-based resumes**, which is 99% of real resumes.
- **MIT/permissive licenses**, unlike some GPL alternatives.

**Why not the alternatives:**
- **PyMuPDF:** higher fidelity but AGPL-licensed (a problem for many use cases) and heavier.
- **Cloud OCR:** overkill and costly; resumes are digital text, not scanned images. We only need OCR for scanned PDFs, which are rare.

**Trade-off accepted:** PDF text extraction sometimes emits icon-font junk. We handle that in `_clean_text()` (stripping Private-Use-Area glyphs) rather than adopting a heavier library.

---

### 🔧 pytest — testing

**Job here:** ([backend/tests/](../backend/tests/)) 13 tests covering the engines, agents, and API — all **deterministic** (no network, no real LLM).

**Alternatives considered:** `unittest` (stdlib), `nose2`.

**Why we chose this:**
- **Fixtures** (`conftest.py`) give clean, isolated in-memory DBs per test run.
- **Plain `assert`** — no `self.assertEqual` ceremony.
- **Huge plugin ecosystem** (`pytest-cov`, `pytest-asyncio`).
- **The whole suite is offline:** tests force the hashing-embedder and mock job providers, so they're fast and never flaky.

**Why not the alternatives:** `unittest` is more verbose and has a weaker fixture model; pytest is the de-facto standard.

---

## Part 2 — AI / LLM / Agents

This is the heart of the project and where the most interesting choices live.

### 🔧 LangGraph — multi-agent orchestration

**Job here:** ([graph.py](../backend/app/agents/graph.py)) Wires the **9 agents** into a stateful graph (nodes + edges), runs them in order, and merges each agent's output into a shared state.

**Alternatives considered:** Raw LangChain chains/`SequentialChain`, CrewAI, Microsoft AutoGen, a hand-written `for`-loop orchestrator.

**Why we chose this:**
- **State-machine model fits the problem.** Job hunting *is* a pipeline: parse → discover → match → score → optimize → write → plan. LangGraph models this as an explicit graph you can read, extend, and visualize.
- **Reducers for free observability.** The `Annotated[list, add]` reducer on `execution_history` means every node appends its own trace entry and you get a full timeline with zero extra code. (See [state.py](../backend/app/agents/state.py).)
- **Partial-state updates.** Each node returns only the keys it changed; LangGraph merges them. Agents stay decoupled.
- **Two graphs from the same nodes.** `build_graph()` (full 9-agent) and `build_analysis_graph()` (lean 4-agent) reuse identical node functions — composability you'd hand-roll painfully otherwise.
- **It's the LangChain team's official answer** for stateful, multi-step agent workflows → best docs and longevity.

**Why not the alternatives:**
- **Raw LangChain `SequentialChain`:** linear only, clumsy state passing, no built-in trace accumulation. LangGraph is purpose-built for exactly this.
- **CrewAI / AutoGen:** designed around *autonomous agents that converse and decide their own order*. We want a **deterministic, ordered pipeline** for reproducible results — conversational autonomy would make scoring non-reproducible and harder to test. They're also heavier and more opinionated.
- **Hand-written loop:** you'd reinvent state merging, error isolation, and tracing. LangGraph gives those as primitives.

**Trade-off accepted:** A dependency and a learning curve. Worth it: the graph is the project's signature architecture.

---

### 🔧 LangChain (core) — the LLM abstraction layer

**Job here:** ([llm.py](../backend/app/core/llm.py), [base.py](../backend/app/agents/base.py)) Provides the provider-agnostic `BaseChatModel` / `Embeddings` interfaces and the message types (`SystemMessage`, `HumanMessage`) the agents use.

**Alternatives considered:** Calling the OpenAI SDK directly everywhere, `litellm`, `instructor`.

**Why we chose this:**
- **Provider independence.** Agents call `get_chat_model().invoke([...])` and never know whether it's Azure OpenAI or local Ollama. Switching is one env var (`LLM_PROVIDER`). The agents are untouched.
- **It's LangGraph's native model interface** — using anything else would mean adapters.
- **Embeddings abstraction** lets us wrap the real provider with a fallback (`_ResilientEmbeddings`).

**Why not the alternatives:**
- **Raw OpenAI SDK everywhere:** would hard-couple every agent to Azure, making the Ollama path and the test fallbacks far messier.
- **litellm:** good router, but redundant once LangChain already abstracts providers and LangGraph expects LangChain models.

**Trade-off accepted:** LangChain is a large dependency with a fast-moving API. We pin exact versions to stay stable.

---

### 🔧 Azure OpenAI (GPT-4o) — the LLM itself

**Job here:** The actual "intelligence." It parses resumes ([resume_agent.py](../backend/app/agents/resume_agent.py)), extracts job skills ([job_skills.py](../backend/app/tools/job_skills.py)), rewrites resumes, writes cover letters, and builds the roadmap.

**Alternatives considered:** OpenAI direct, Anthropic Claude, Google Gemini, local models via Ollama (Llama 3, Mistral).

**Why we chose this (for this deployment):**
- **Enterprise/Azure integration.** Azure OpenAI offers the same GPT-4o model with enterprise networking, regional data residency, and a corporate-friendly endpoint — which is exactly the environment this was built in.
- **GPT-4o quality** for structured extraction (reliable JSON) and natural writing (cover letters) in one model.
- **The code is provider-agnostic anyway.** Thanks to the LangChain abstraction, swapping to OpenAI-direct or Anthropic is trivial.

**Why the design also supports Ollama:**
- **Zero-cost local dev / offline demos.** `LLM_PROVIDER=ollama` runs Llama 3 on your laptop — no API key, no per-token cost, full privacy. Great for development and for users who can't use cloud AI.

**Why not lock to one:**
- Hard-coding any single vendor is a portability and cost risk. The factory pattern in `llm.py` keeps you free.

**Trade-off accepted:** Cloud LLM calls cost money and add latency. Mitigated by: low temperatures (cheap, deterministic), caching job-skill extraction, rate limiting, and the Ollama escape hatch.

---

### 🔧 ChromaDB — the vector database

**Job here:** ([store.py](../backend/app/vector/store.py)) Stores embeddings of resume sections and job descriptions so the matching layer can do **semantic** (meaning-based) retrieval, not just keyword matching.

**Alternatives considered:** Pinecone, Weaviate, Qdrant, FAISS, `pgvector` (Postgres extension).

**Why we chose this:**
- **Embedded mode = zero infrastructure.** ChromaDB runs in-process and persists to a local directory (`./.chroma`). No separate server, no account, no cost — perfect for a self-contained app you can clone and run.
- **Dead-simple API:** `collection.upsert(...)` / `collection.query(...)`.
- **Good enough scale.** For one user's resume sections and a few hundred jobs, you don't need a distributed vector DB.

**Why not the alternatives:**
- **Pinecone/Weaviate:** managed, scalable, excellent — but require an account, API key, network calls, and (Pinecone) money. Overkill here.
- **FAISS:** blazing fast and local, but it's a *library*, not a database — no persistence, metadata, or collections out of the box. You'd build a storage layer around it.
- **pgvector:** elegant if you're already on Postgres, and a natural future upgrade — but it couples vector search to the relational DB and needs the extension installed. Chroma keeps the concern isolated.

**Trade-off accepted:** Embedded Chroma won't scale to millions of vectors across many nodes. The clean `VectorStore` wrapper means swapping to Pinecone/pgvector later touches one file.

---

### 🔧 The "resilient embeddings" + hashing fallback — a custom design

**Job here:** ([llm.py](../backend/app/core/llm.py)) `_ResilientEmbeddings` wraps the real embedder; if the network fails (e.g. behind an SSL proxy, or no embedding deployment configured), it transparently switches to `_HashingEmbeddings` — a dependency-free deterministic embedder.

**Why this exists (and why it's clever):**
- **The app must never hard-crash** because an embedding call failed. Semantic ranking degrades gracefully to a hash-based approximation instead of returning a 500.
- **Tests run fully offline** by forcing the hashing embedder — fast and never flaky.

This is a **graceful-degradation** pattern you'll see repeated throughout the codebase.

---

## Part 3 — Database & persistence

### 🔧 SQLAlchemy 2.0 (ORM) — database access

**Job here:** ([models.py](../backend/app/db/models.py), [session.py](../backend/app/db/session.py)) Maps Python classes to DB tables, manages sessions, and lets the service layer query with Python instead of SQL strings.

**Alternatives considered:** Raw SQL (`sqlite3`/`psycopg2`), `Django ORM`, `Tortoise ORM`, `SQLModel`, `Peewee`.

**Why we chose this:**
- **Database-agnostic.** The *same* model code runs on **SQLite in dev** and **PostgreSQL in prod** — change one env var (`DATABASE_URL`). This is the single biggest reason: zero-setup local dev, real DB in production.
- **2.0's typed `Mapped[...]` syntax** gives IDE autocomplete and type checking on every column.
- **Relationships & cascades** (`relationship(..., cascade="all, delete-orphan")`) model the User→Resume→Skill graph cleanly.
- **Session/Unit-of-Work pattern** with `get_db()` guarantees connections are always closed.
- **It's the Python ORM standard** — the most documented, most stable choice.

**Why not the alternatives:**
- **Raw SQL:** maximum control, but you'd hand-write CRUD, manage connections, and lose type safety. For a CRUD-heavy app, the ORM saves enormous boilerplate.
- **Django ORM:** excellent, but tied to Django — can't use it standalone with FastAPI cleanly.
- **SQLModel:** lovely (Pydantic + SQLAlchemy combined), but younger and it merges two concerns (DB model + API schema) that this project deliberately keeps separate (ORM models vs Pydantic schemas).
- **Tortoise/Peewee:** smaller ecosystems, weaker async/typing stories.

**Trade-off accepted:** ORMs add a learning curve and can hide expensive queries. For this scale, clarity wins.

---

### 🔧 SQLite (dev) + PostgreSQL (prod) — the database engine(s)

**Job here:** Stores users, resumes, jobs, matches, scores, applications, and run logs.

**Why two databases, and why these:**
- **SQLite for development** = **zero setup**. It's a single file (`talenttrail.db`), ships with Python, needs no server. Clone the repo and it just runs. Perfect for learning and for the test suite (in-memory SQLite).
- **PostgreSQL for production** = the gold-standard relational DB: concurrent writes, JSON columns, full-text search, robust indexing, battle-tested at scale. The Docker setup uses `postgres:16`.

**Alternatives considered:** MySQL, MongoDB, staying on SQLite in prod.

**Why not the alternatives:**
- **MongoDB (document DB):** the data here is highly **relational** (users own resumes own skills; jobs have matches and scores). Foreign keys and joins are natural — forcing it into documents would lose integrity guarantees. We use **JSON columns** for the genuinely semi-structured bits (parsed resume, keyword analysis) and get the best of both.
- **MySQL:** fine, but Postgres has superior JSON support and is the common default in the Python world.
- **SQLite in prod:** struggles with concurrent writes and lacks the operational tooling of Postgres.

**Why SQLAlchemy makes this painless:** because the ORM abstracts the dialect, supporting both is literally a `DATABASE_URL` change plus the `check_same_thread` flag for SQLite (handled in [session.py](../backend/app/db/session.py)).

**Trade-off accepted:** Subtle dialect differences exist (e.g. JSON behavior). The schema deliberately stays simple to avoid them.

---

### 🔧 JSON columns — a deliberate modeling choice

**Job here:** Columns like `Resume.parsed`, `JobPosting.skills`, `KeywordAnalysis.missing`, and `JobMatch.explanation` store semi-structured data as JSON.

**Why:**
- **LLM output evolves.** If the resume parser later adds a field, you don't need a database migration — the JSON column absorbs it.
- **It avoids dozens of tiny tables** for inherently nested data (a parsed resume is a tree, not a grid).

**Why not fully normalize everything:** you'd need a migration every time a prompt changes, and reconstructing a nested resume from 8 joined tables is painful. The hybrid (relational core + JSON for AI output) is the pragmatic sweet spot.

---

## Part 4 — Frontend

### 🔧 React 18 — the UI library

**Job here:** Renders every screen — the guided AI Assistant flow, the autopilot timeline, dashboards, the Kanban board.

**Alternatives considered:** Vue, Angular, Svelte, server-rendered templates (Jinja).

**Why we chose this:**
- **Component model fits a dashboard app** with many reusable pieces (ATS card, keyword table, charts, board).
- **Largest ecosystem** — Recharts, lucide-react, React Router, Testing Library all just work.
- **Most in-demand skill** for a portfolio project; reviewers know React.
- **Hooks** (`useState`, `useEffect`, `useContext`) give clean state logic without classes.

**Why not the alternatives:**
- **Angular:** powerful but heavyweight and opinionated — too much framework for this size.
- **Svelte:** elegant and fast, but smaller ecosystem and less industry demand.
- **Vue:** great, genuinely comparable — React was chosen for ecosystem size and ubiquity.
- **Server-rendered templates:** would couple UI to the backend and lose the rich, app-like interactivity (drag-drop board, live pipeline animation).

**Trade-off accepted:** React needs a build step and more boilerplate than Svelte. The ecosystem payoff is worth it.

---

### 🔧 Vite — the build tool & dev server

**Job here:** ([vite.config.js](../frontend/vite.config.js)) Runs the dev server (`npm run dev`) with instant hot-reload and produces the optimized production bundle (`npm run build`).

**Alternatives considered:** Create React App (CRA), webpack (hand-configured), Parcel, Next.js.

**Why we chose this:**
- **Instant startup & hot module replacement** via native ES modules — no waiting for a full bundle on every save.
- **Fast production builds** (esbuild + Rollup) — the whole app builds in ~1.6s.
- **`import.meta.env.VITE_*`** for build-time env injection (how `VITE_API_BASE_URL` gets baked in).
- **Zero-config** for React + TS.

**Why not the alternatives:**
- **CRA:** effectively deprecated, slow, and unmaintained.
- **Hand-rolled webpack:** powerful but a config rabbit hole.
- **Next.js:** fantastic, but it's a *full-stack* framework with SSR/routing/server functions. We already have a FastAPI backend — Next.js would duplicate that role and over-complicate the split. We want a **pure SPA** talking to a separate API.

**Trade-off accepted:** Vite's dev (esbuild) and prod (Rollup) use different bundlers, so rare edge-case differences can appear. Not encountered here.

---

### 🔧 React Router v6 — client-side routing

**Job here:** ([App.jsx](../frontend/src/App.jsx)) Maps URLs (`/ats`, `/tracker`, `/auto`) to page components, guards protected routes, and redirects unauthenticated users to `/login`.

**Alternatives considered:** TanStack Router, hand-rolled `switch` on `window.location`, Next.js routing.

**Why we chose this:**
- **The standard for React SPAs** — declarative `<Routes>`/`<Route>`, nested layouts, `<Navigate>` for redirects.
- **The `<Protected>` wrapper pattern** (auth gate) composes naturally with it.

**Why not the alternatives:** TanStack Router is newer/typed but adds complexity we don't need; hand-rolling routing means reinventing history handling.

---

### 🔧 Tailwind CSS — styling

**Job here:** ([tailwind.config.js](../frontend/tailwind.config.js), every `.jsx`) All styling, including dark mode and the brand gradient.

**Alternatives considered:** plain CSS / CSS Modules, styled-components (CSS-in-JS), Material UI / Chakra / Ant Design.

**Why we chose this:**
- **Speed.** Utility classes (`flex h-screen bg-slate-50 dark:bg-slate-950`) let you build polished UI without context-switching to CSS files.
- **Dark mode is trivial** — `dark:` variants + `darkMode: "class"`. The app's whole dark theme is just these variants.
- **Consistent design tokens.** Spacing, colors, and typography come from one scale, so the UI looks coherent without a designer.
- **No unused CSS.** Tailwind purges everything you don't use → tiny CSS bundle (~40 KB).

**Why not the alternatives:**
- **Component libraries (MUI/Chakra):** give you pre-built components fast, but impose *their* look, are heavy, and are hard to customize deeply. We wanted a custom-branded UI.
- **styled-components:** runtime CSS-in-JS adds a performance cost and a different mental model.
- **Plain CSS:** total control, but slow to build with and easy to make inconsistent.

**Trade-off accepted:** Class strings get long and look busy in JSX. The build-speed and consistency wins dominate.

---

### 🔧 Axios — HTTP client (frontend)

**Job here:** ([api.js](../frontend/src/lib/api.js)) The single place that talks to the backend. Injects the JWT on every request and handles 401s globally.

**Alternatives considered:** native `fetch`, TanStack Query, SWR.

**Why we chose this:**
- **Interceptors.** Axios lets you attach the `Authorization` header on *every* request and redirect on *every* 401 in one place — `fetch` has no built-in interceptors, so you'd wrap it yourself.
- **Ergonomics:** automatic JSON parsing, `baseURL`, `params`, timeouts (used for the 180s pipeline call).

**Why not the alternatives:**
- **fetch:** capable but lower-level; you'd re-implement interceptors, JSON handling, and timeouts.
- **TanStack Query/SWR:** excellent for caching/refetching server state, but they're *data-fetching state managers*, not HTTP clients — heavier than this app's straightforward request/response needs. (A natural future upgrade.)

**Trade-off accepted:** One dependency over the built-in `fetch`. The interceptor model pays for itself immediately (auth + 401 handling live in ~10 lines).

---

### 🔧 Recharts — charts

**Job here:** ([AnalyticsCharts.jsx](../frontend/src/components/AnalyticsCharts.jsx)) Renders the dashboard analytics (applications over time, status funnel, skill gaps, source performance).

**Alternatives considered:** Chart.js, D3 directly, Victory, Nivo.

**Why we chose this:**
- **React-native API.** Charts are declared as JSX components (`<LineChart><Line/></LineChart>`) — fits the React model perfectly.
- **Sensible defaults** look good with little config, and it's responsive out of the box.
- **Dark-mode friendly** — we drive axis/grid colors from a `useDarkMode()` hook.

**Why not the alternatives:**
- **D3:** ultimate power, steep learning curve, imperative — overkill for standard charts.
- **Chart.js:** canvas-based and not React-idiomatic (needs a wrapper).
- **Nivo/Victory:** comparable; Recharts chosen for simplicity and popularity.

**Trade-off accepted:** Recharts is less customizable than raw D3. We don't need exotic visualizations.

---

### 🔧 lucide-react — icons

**Job here:** Clean SVG icons across the UI.

**Why:** Tree-shakeable (only the icons you import ship), consistent stroke style, MIT-licensed, and the de-facto successor to Feather icons. Alternatives (FontAwesome, Material Icons) are heavier or stylistically inconsistent with the design.

---

## Part 5 — DevOps & infrastructure

### 🔧 Docker + Docker Compose — packaging & local orchestration

**Job here:** ([docker-compose.yml](../docker-compose.yml)) Packages the three services — **Postgres**, **FastAPI backend**, **React/nginx frontend** — so the whole stack runs identically on any machine with one command: `docker compose up`.

**Alternatives considered:** "just install everything manually," a Python venv + local Postgres, Vagrant/VMs, Kubernetes.

**Why we chose this:**
- **"Works on my machine" → "works on every machine."** Docker pins OS, Python, Node, and system libs, so the app behaves the same on your laptop, a colleague's, and AWS.
- **Compose models multi-service apps** (db + backend + frontend + networks + volumes) declaratively.
- **The exact thing the user asked about** — "run this on another laptop / deploy to cloud." Docker is the answer.

**Why not the alternatives:**
- **Manual install:** brittle, slow, and the source of environment drift.
- **VMs/Vagrant:** heavier and slower than containers for the same isolation.
- **Kubernetes:** the right tool at scale, but massive overkill for a single-node app. The project provides a Compose overlay (`docker-compose.aws.yml`) for a single EC2 box instead — far simpler and free-tier friendly.

**Trade-off accepted:** Docker adds a build step and image size to manage. The portability is the entire point of the deployment story.

---

### 🔧 nginx — production web server & reverse proxy

**Job here:** ([nginx.conf](../frontend/nginx.conf)) In production, nginx (a) serves the **static built React app** and (b) **proxies `/api/*` to the backend** container.

**Alternatives considered:** serving React from Vite's preview server, serving static files from FastAPI, Caddy, Traefik.

**Why we chose this:**
- **Fast static serving** — nginx is purpose-built for it.
- **The `/api` proxy eliminates CORS in production.** Because the browser sees one origin (nginx) and nginx forwards `/api` internally to `backend:8000`, there are no cross-origin requests at all. This solved a real production bug.
- **SPA fallback:** unknown routes return `index.html` so client-side routing works on refresh.

**Why not the alternatives:**
- **Vite preview:** a dev tool, not a hardened production server.
- **FastAPI serving static files:** possible, but couples concerns and wastes Python workers on static assets nginx serves better.
- **Caddy/Traefik:** great (auto-HTTPS!), valid alternatives — nginx chosen for ubiquity and the team's familiarity.

**Trade-off accepted:** nginx config syntax is its own thing to learn. The CORS-elimination and performance wins justify it.

---

### 🔧 GitHub Actions — CI/CD

**Job here:** ([.github/workflows/](../.github/workflows/)) `ci.yml` runs backend tests + frontend build on every push; `deploy.yml` SSH-deploys to EC2.

**Alternatives considered:** GitLab CI, CircleCI, Jenkins, manual deploys.

**Why we chose this:**
- **Native to GitHub** where the code lives — zero extra accounts.
- **Free tier** generous enough for a portfolio project.
- **Simple YAML** workflows; huge marketplace of prebuilt actions (`appleboy/ssh-action` for deploy).

**Why not the alternatives:**
- **Jenkins:** self-hosted, heavyweight, a server to babysit.
- **CircleCI/GitLab CI:** fine, but another platform when GitHub already hosts the repo.

**Trade-off accepted:** Vendor lock-in to GitHub. Acceptable for a GitHub-hosted project.

---

## Part 6 — The "why" of the architecture itself

Beyond individual libraries, the project makes a few **structural** choices worth justifying:

### Layered (clean) architecture: `API → Service → Agents/Engines/Tools → Data`
**Why:** Each layer is independently testable and swappable. Endpoints handle HTTP only; the **service layer** ([copilot_service.py](../backend/app/services/copilot_service.py)) owns business logic and is the *only* place that touches the DB; agents/engines stay pure. You could swap FastAPI for another framework and the business logic wouldn't change.

### Separation of ORM models from API schemas
**Why:** [models.py](../backend/app/db/models.py) (database) and [schemas.py](../backend/app/schemas.py) (API contract) are deliberately separate. Changing a DB column doesn't silently change your public API, and vice versa. This is why SQLModel (which merges them) was *not* used.

### Deterministic engines vs LLM agents
**Why:** Scoring (ATS, keyword, matching) is **pure math** in [tools/](../backend/app/tools/) — reproducible, unit-tested, explainable. Judgment (parsing, writing, planning) is delegated to the **LLM**. This split means scores are defensible (not a black box) and the math is testable without a network. The LLM enriches; the math decides.

### Graceful degradation everywhere
**Why:** LLM down → deterministic fallback. Embeddings down → hashing embedder. Live jobs down → mock providers. One agent errors → the `@track` decorator records it and the graph continues. The app is designed to **bend, not break**.

---

## One-page cheat sheet

| Layer | Tech | Chosen over | Deciding reason |
|---|---|---|---|
| Language | **Python 3.12** | Node, Go, Java | AI ecosystem is Python-first |
| API | **FastAPI** | Flask, Django, Express | Async + Pydantic validation + auto docs |
| Validation/Config | **Pydantic v2** | dataclasses, marshmallow | One model = validate + serialize + docs |
| Auth | **JWT (jose) + bcrypt** | sessions, Auth0 | Stateless, no session store, no vendor |
| Rate limit | **slowapi** | Redis limiter, nginx | In-process, zero infra |
| Logging | **structlog** | stdlib, loguru | Structured JSON for aggregation |
| HTTP | **httpx** | requests, aiohttp | Sync+async + custom SSL control |
| Parsing | **pypdf / python-docx** | PyMuPDF, OCR | Pure-Python, no native deps, permissive license |
| Orchestration | **LangGraph** | CrewAI, AutoGen, raw loop | Deterministic state-machine + free tracing |
| LLM abstraction | **LangChain** | raw OpenAI SDK | Provider-agnostic, LangGraph-native |
| LLM | **Azure OpenAI GPT-4o** | OpenAI, Claude, Gemini | Enterprise Azure + provider-swappable |
| Local LLM | **Ollama** (optional) | — | Free, offline, private dev |
| Vectors | **ChromaDB** | Pinecone, FAISS, pgvector | Embedded, zero infra, simple API |
| ORM | **SQLAlchemy 2.0** | raw SQL, Django ORM, SQLModel | DB-agnostic, typed, standard |
| DB (dev) | **SQLite** | — | Zero setup, single file |
| DB (prod) | **PostgreSQL** | MySQL, MongoDB | Relational + JSON, scales |
| UI | **React 18** | Vue, Angular, Svelte | Ecosystem + demand + components |
| Build | **Vite** | CRA, webpack, Next.js | Instant HMR, fast builds, pure SPA |
| Routing | **React Router v6** | TanStack, hand-rolled | Standard, composable guards |
| Styling | **Tailwind** | MUI, styled-components | Speed + dark mode + tiny bundle |
| HTTP (FE) | **Axios** | fetch, TanStack Query | Interceptors for JWT + 401 |
| Charts | **Recharts** | Chart.js, D3 | React-idiomatic, good defaults |
| Icons | **lucide-react** | FontAwesome | Tree-shakeable SVGs |
| Container | **Docker + Compose** | manual, VMs, K8s | Portable, multi-service, free-tier deploy |
| Web server | **nginx** | Vite preview, Caddy | Fast static + `/api` proxy kills CORS |
| CI/CD | **GitHub Actions** | Jenkins, CircleCI | Native to repo, free, simple YAML |

---

**Next:** read [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md) for a line-by-line explanation of how all this code actually works and links together.
