# RepoPilot — RAG-Based AI Engineering Copilot

RepoPilot is an enterprise-grade AI Engineering Copilot powered by Retrieval-Augmented Generation (RAG), hybrid retrieval, cross-encoder reranking, and specialized LangGraph agents. It connects to GitHub repositories (or local codebases), indexes their source code and documentation using code-aware AST parsers, and enables software engineers to investigate architectures, debug production errors, audit security vulnerabilities, and receive precise, grounded answers with exact source line citations.

---
project live link : https://ripe-charlie-packing-heaven.trycloudflare.com/

## 1. System Architecture

RepoPilot separates retrieval, reasoning, and presentation into loosely coupled, observable layers:

```
                                  ┌───────────────────────────┐
                                  │      Developer Client     │
                                  └─────────────┬─────────────┘
                                                │ (Next.js 14 + Monaco Editor)
                                                ▼
                                  ┌───────────────────────────┐
                                  │    FastAPI Application    │
                                  └─────────────┬─────────────┘
                                                │
                      ┌─────────────────────────┴─────────────────────────┐
                      │                                                   │
                      ▼                                                   ▼
         ┌─────────────────────────┐                         ┌─────────────────────────┐
         │ Ingestion & Processing  │                         │ AI & RAG Query Pipeline │
         └────────────┬────────────┘                         └────────────┬────────────┘
                      │                                                   │
      ┌───────────────┼───────────────┐                   ┌───────────────┼───────────────┐
      │               │               │                   │               │               │
      ▼               ▼               ▼                   ▼               ▼               ▼
┌───────────┐   ┌───────────┐   ┌───────────┐       ┌───────────┐   ┌───────────┐   ┌───────────┐
│ Git Tree  │   │ Code AST  │   │ Normalized│       │   Query   │   │  Hybrid   │   │  Cross-   │
│ Scanner   │   │  Parser   │   │ Embeddings│       │ Rewriter  │   │ Retriever │   │  Encoder  │
└───────────┘   └───────────┘   └───────────┘       └───────────┘   └───────────┘   └───────────┘
                      │                                                   │
                      ▼                                                   ▼
         ┌─────────────────────────┐                         ┌─────────────────────────┐
         │ PostgreSQL + pgvector   │ ◄───────────────────────┤   Context Builder &     │
         │ (Code Chunks & Vectors) │                         │   Token Budgeting       │
         └─────────────────────────┘                         └────────────┬────────────┘
                                                                          │
                                                                          ▼
                                                             ┌─────────────────────────┐
                                                             │   LangGraph Agents      │
                                                             │ (Debug, Security, Arch) │
                                                             └────────────┬────────────┘
                                                                          │
                                                                          ▼
                                                             ┌─────────────────────────┐
                                                             │ Grounded SSE Generator  │
                                                             │ (Line Citations in UI)  │
                                                             └─────────────────────────┘
```

---

## 2. Key Features

- **Code-Aware Syntax Chunking**: Preserves logical AST units (functions, classes, methods, docstrings, configuration steps) across Python, TypeScript, JavaScript, Go, Rust, Java, C++, Markdown, YAML, Dockerfiles, and Shell scripts.
- **Hybrid Retrieval & Reciprocal Rank Fusion (RRF)**:
  - Vector similarity search (pgvector cosine distance)
  - BM25 lexical keyword matching
  - Metadata filtering (repository, branch, language, symbol type, file path)
  - Reciprocal Rank Fusion ($Score(d) = \sum \frac{1}{60 + rank}$)
- **Cross-Encoder Reranking**: Evaluates query-code relevance, exact symbol matches, HTTP status codes (e.g. 401, 500), and path significance before passing top candidates to context builder.
- **Context Builder & Line Grounding**: Deduplicates code, groups by file, formats line windows (`start_line-end_line`), and enforces strict token budgets.
- **Monaco Editor Source Viewer**: Clicking any evidence citation pill (e.g. `[backend/auth/middleware.py:20-52]`) immediately loads the file and highlights the cited line span.
- **Specialized LangGraph Agents**:
  - **Debug Agent**: Traces exceptions, HTTP status codes, and execution paths to diagnose root causes and suggest unit tests.
  - **Security Agent**: Audits hardcoded credentials, JWT secret fallbacks, and token revocation mechanisms.
  - **Architecture Agent**: Outlines system layers, dependency flows, and framework initialization.
  - **DevOps Agent**: Inspects Dockerfile steps, compose environment variables, and deployment configurations.
  - **Code Agent**: Explains function signatures, type invariants, and implementation patterns.
  - **Documentation Agent**: Generates API references and onboarding walkthroughs.
- **Automated RAG Benchmarking**: Built-in evaluation dashboard measuring **Context Precision**, **Context Recall**, **Answer Relevance**, **Faithfulness**, latency, and token cost.
- **Incremental Indexing**: Uses SHA256 content hashing to re-index only changed files upon GitHub commit webhooks.

---

## 3. Technology Stack & Design Decisions

| Component | Selected Technology | Technical Rationale |
| :--- | :--- | :--- |
| **Frontend Framework** | **Next.js 14 (App Router)** | Server-side rendering, streaming SSE support, and modular TypeScript components. |
| **Code Viewer** | **Monaco Editor** | The industry standard for developer tooling; supports multi-language syntax highlighting, line decorations, and line jump APIs. |
| **Backend API** | **FastAPI + AsyncIO** | High-throughput asynchronous request handling, native OpenAPI docs, and native SSE streaming. |
| **Database & Vector Store**| **PostgreSQL + pgvector** | Eliminates vector-store sync drift; stores relational models, conversation state, and embeddings in one ACID-compliant engine. |
| **Agent Orchestration** | **LangGraph** | Explicit cyclical and conditional graph control flow with state typed schemas for multi-agent routing. |
| **Lexical Search** | **BM25Okapi** | Provides exact token and identifier matches for functions, error codes, and variable names that semantic embeddings miss. |
| **Reranking** | **Multi-Factor Cross Scorer** | Reranks hybrid search candidates based on lexical overlap, symbol identity, and file path importance. |

---

## 4. Repository Ingestion Pipeline

When a GitHub repository URL or local directory is submitted:
1. **Scanning**: Resolves git tree via the GitHub REST API or local directory walker.
2. **File Filtering**: Ignores lockfiles, binaries, minified bundles, and vendor directories.
3. **Language Detection & AST Parsing**: Dispatches files to language-specific parsers. Python files are parsed using the standard `ast` module to record exact start and end line ranges for classes, methods, and functions.
4. **Metadata Extraction**: Computes SHA256 content hashes, symbol names, and parent scopes.
5. **Embedding Generation**: Generates 384-dimensional normalized vector embeddings.
6. **Persistence**: Writes chunks and vectors into `code_chunks` with pgvector index.

---

## 5. End-to-End Demo Scenario

A complete demo repository is included under `examples/sample-repo`.

### The Scenario:
A developer asks: **"Why is the login endpoint returning 401?"**

### RepoPilot's Execution:
1. **Query Understanding**: Classifies the query as `debug`, notes HTTP status code `401` and term `login`. Rewrites search queries to include `verify_jwt_token`, `AuthenticationMiddleware`, and `JWT_SECRET`.
2. **Router**: Activates the **Debug Agent**.
3. **Hybrid Search**: Retrieves candidate chunks from `backend/auth/middleware.py`, `backend/config/settings.py`, and `backend/routes/auth.py`.
4. **Reranker**: Prioritizes `AuthenticationMiddleware` and `settings.JWT_SECRET` due to exact 401 response and symbol alignment.
5. **Context Builder**: Packages lines 20-52 of `middleware.py` and settings into an evidence block.
6. **Streaming Response**: Generates a structured analysis with:
   - **Answer**
   - **Evidence**: `backend/auth/middleware.py:20-52` and `backend/config/settings.py:10-28`
   - **Root Cause**: Missing or malformed `Authorization: Bearer <token>` header, or missing `JWT_SECRET` in Docker environment variables.
   - **Suggested Fix**: Update `docker-compose.yml` to supply `JWT_SECRET`.
   - **Recommended Tests**: Unit tests verifying 401 on empty header and 200 on valid bearer token.
7. **Monaco Editor**: Clicking the citation badge jumps directly to lines 20-52 of `backend/auth/middleware.py` with visual highlight.

---

## 6. Quick Start & Docker Deployment

### Prerequisites
- Docker & Docker Compose **OR** Python 3.11+ and Node.js 18+

### Running with Docker Compose (Recommended)
```bash
# 1. Clone repository
git clone https://github.com/user/RepoPilot.git
cd RepoPilot

# 2. Configure environment
cp .env.example .env

# 3. Start entire stack (Frontend, Backend, Worker, PostgreSQL+pgvector, Redis)
docker compose up --build
```
- Frontend UI: `http://localhost:3000`
- FastAPI Swagger Docs: `http://localhost:8000/docs`

---

### Running Locally (Without Docker)

#### Backend:
```bash
# 1. Create and activate virtual environment
python -m venv backend/venv
# Windows:
.\backend\venv\Scripts\activate
# Linux/macOS:
source backend/venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Start backend API (Automatically falls back to local SQLite if PostgreSQL is not active)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## 7. Running Backend & Integration Tests

```bash
# Run complete test suite (Chunking, AST parsing, RAG retriever, API lifecycle)
pytest backend/tests -v
```

---

## 8. API Reference

- `POST /api/repositories`: Register a new repository for indexing.
- `GET /api/repositories`: List indexed repositories and status.
- `GET /api/repositories/{id}/index-status`: Poll real-time indexing percentage and status.
- `GET /api/repositories/{id}/files-tree`: Retrieve hierarchical file tree for Monaco explorer.
- `GET /api/repositories/{id}/files-content?path=...`: Fetch raw code for Monaco Editor.
- `POST /api/chat/stream`: Server-Sent Events (SSE) streaming endpoint for grounded answers with line citations.
- `POST /api/agents/run`: Execute specialized LangGraph multi-step agent.
- `POST /api/evaluations/run`: Run RAG benchmarking test suite.
- `POST /api/github/webhook`: Ingest GitHub commit push events for incremental diff re-indexing.

---

## 9. Live Cloud Deployment (Render Blueprint)

RepoPilot includes an automated [`render.yaml`](./render.yaml) blueprint specification for 1-click full-stack deployment (PostgreSQL + pgvector, Redis, FastAPI Backend, and Next.js Frontend).

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/infant88/RepoPilot)

### Deployment Steps:
1. Click the **Deploy to Render** button above or go to [dashboard.render.com/blueprints](https://dashboard.render.com/blueprints).
2. Connect your GitHub repository (`https://github.com/infant88/RepoPilot`).
3. Render automatically provisions:
   - **PostgreSQL Database** with vector extension support.
   - **Redis Instance** for caching & asynchronous task queues.
   - **FastAPI Backend Web Service** (Docker container running Uvicorn).
   - **Next.js Frontend Web Service** (Node 20 production build).
4. Enter your `LLM_API_KEY` (e.g., Google Gemini or OpenAI API Key).
5. Set `NEXT_PUBLIC_API_URL` on the frontend service to `https://<your-backend-service-name>.onrender.com/api`.
6. Your live RepoPilot instance is online and accessible globally over HTTPS!

