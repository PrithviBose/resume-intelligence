# Resume Intelligence

An AI engineering learning project: upload a resume, extract structured profile data, semantically search its contents, and chat with it through transparent RAG pipelines — with observability and offline quality evaluation.

Built to understand how production RAG systems work end-to-end, not just call an API wrapper.

## Features

- **Resume ingestion** — PDF/DOCX upload, text extraction, chunking, and embedding into ChromaDB
- **Profile extraction** — LLM extracts name, email, company, and experience into PostgreSQL
- **Semantic search** — raw vector search over resume chunks (`/api/search`)
- **Fixed-chain RAG chat** — 4-step pipeline: understand → retrieve → analyze → synthesize (`/api/query`)
- **Agentic AI chat** — tool-calling agent loop; the LLM decides when to search the resume or fetch contact info (`/api/query/agent`)
- **Langfuse tracing** — `@observe()` spans on every LLM step for debugging latency and cost
- **RAGAS evaluation** — standalone offline script scores answer quality against a hand-written golden set

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Frontend | Next.js 16, React 19, Tailwind CSS |
| LLM | Azure OpenAI (structured outputs + tool calling) |
| Embeddings | `sentence-transformers` (BAAI/bge-small-en-v1.5) |
| Vector DB | ChromaDB |
| Database | PostgreSQL |
| Observability | Langfuse |
| Evaluation | RAGAS |

## Architecture

```
Upload (PDF/DOCX)
    → parse & chunk → embed → ChromaDB
    → LLM profile extraction → PostgreSQL

Query time (fixed chain):
    understand question → vector search → analyze evidence → synthesize answer

Query time (agent):
    LLM loop → [search_resume | get_candidate_contact_info] → final answer
```

Both chat modes expose their reasoning in the UI (prompt chain steps or tool calls). Every LLM call is traced in Langfuse.

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- Azure OpenAI resource (API key + deployment)

## Quick Start

### 1. Start infrastructure

```bash
docker compose up -d
```

This starts:
- **PostgreSQL** — `localhost:5432`
- **ChromaDB** — `localhost:8001`
- **Chroma Admin UI** — `http://localhost:3001`

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # fill in Azure OpenAI credentials
uvicorn app.main:app --reload --port 8000
```

API docs: `http://127.0.0.1:8000/docs`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:3000`

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and set at minimum:

| Variable | Description |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource URL |
| `AZURE_OPENAI_API_KEY` | API key |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Chat model deployment (e.g. `gpt-4.1-mini`) |
| `DATABASE_URL` | PostgreSQL connection string (default matches docker-compose) |
| `CHROMA_HOST` / `CHROMA_PORT` | ChromaDB address (default `localhost:8001`) |

Optional:

| Variable | Description |
|---|---|
| `LANGFUSE_*` | Enable LLM tracing in Langfuse Cloud |
| `JOB_DESCRIPTION` | Target role JD for candidate-fit checks in `/api/query` |
| `RAGAS_API_BASE_URL` | Base URL for the offline eval script (default `http://127.0.0.1:8000`) |
| `RAGAS_JUDGE_DEPLOYMENT_NAME` | Cheaper model for RAGAS judge LLM (defaults to main deployment) |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/parse` | Upload and ingest a resume |
| `POST` | `/api/search` | Raw semantic search (no LLM) |
| `POST` | `/api/query` | Fixed-chain RAG chat |
| `POST` | `/api/query/agent` | Tool-calling agent chat |
| `GET` | `/api/users` | List uploaded candidates |
| `GET` | `/health` | Health check |

## RAGAS Evaluation

Offline quality scoring for the fixed-chain pipeline. Lives in `backend/eval/` and is **never imported** by the running app.

```bash
# Terminal 1 — backend must be running
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 — fill in eval/golden_set.json first (resume_id + reference answers)
cd backend
python -m eval.run_ragas_eval
```

Scores four metrics per question: **faithfulness**, **answer relevancy**, **context precision**, **context recall**. Results are saved to `backend/eval/results/` as timestamped JSON files.

## Project Structure

```
backend/
├── app/
│   ├── controllers/     # HTTP orchestration
│   ├── services/          # business logic (RAG, agent, embeddings, chunking)
│   ├── routes/            # FastAPI endpoints
│   ├── schemas/           # Pydantic request/response models
│   └── lib/               # config, DB, Chroma, Azure OpenAI
└── eval/                  # standalone RAGAS evaluation (offline only)

frontend/
├── app/(main)/            # pages: upload, chat, agent-chat
├── components/            # UI + debug panels (PromptChainSteps, AgentToolCalls)
└── lib/                   # API client + types

docs/
└── progress.html          # detailed revision notes, diagrams, glossary
```

## What This Project Teaches

- Building a RAG pipeline from scratch (retrieval, prompting, structured outputs)
- Implementing a tool-calling agent loop without LangChain/LangGraph
- Observability with Langfuse (`@observe`, session tracing)
- Measuring RAG quality with RAGAS and a golden dataset
- Separating runtime app code from offline eval tooling

## License

Personal learning project — not licensed for commercial use.
