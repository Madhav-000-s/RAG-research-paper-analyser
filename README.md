# Research Paper Intelligence Engine

A full-stack Retrieval-Augmented Generation (RAG) system for research papers. Upload PDFs, ask questions in natural language, and get answers with **inline citations** that link directly to the source page and section.

Built with hybrid retrieval (dense + sparse + RRF + cross-encoder re-ranking), a citation-enforcing generation pipeline, and an evaluation harness that measures retrieval recall, citation precision, and citation recall.

---

## Features

- **PDF Ingestion** — Parses academic PDFs with PyMuPDF, classifies elements (titles, body text, tables, figure captions), and chunks semantically at 512 tokens with section-boundary respect.
- **Hybrid Retrieval** — Combines dense vector search (pgvector) with sparse keyword search (PostgreSQL `tsvector` BM25), fused via Reciprocal Rank Fusion and re-ranked with a cross-encoder.
- **Citation-Forced Generation** — System prompt enforces `[N]` citation format; a regex parser maps citations back to source chunks with page and section metadata.
- **Multi-Provider LLM** — Ollama (primary, local, GPU-accelerated), with optional Anthropic and OpenAI paths.
- **Interactive UI** — Split-pane Next.js layout: PDF viewer on the left, chat on the right. Clicking a citation jumps the PDF viewer to the cited page.
- **Evaluation Harness** — Measures retrieval recall@k, citation precision, and citation recall against ground-truth QA pairs.

---

## Architecture

```
┌────────────────┐   ┌──────────────────────────────────────────┐   ┌──────────────┐
│   Next.js UI   │◄─▶│              FastAPI Backend             │◄─▶│  PostgreSQL  │
│                │   │                                          │   │  + pgvector  │
│  PDF Viewer  ◄─┤   │  ┌──────────┐  ┌──────────┐  ┌────────┐  │   │              │
│  Chat Panel  ─▶│   │  │Ingestion │  │Retrieval │  │Generate│  │   └──────────────┘
│  Citations  ◄──┤   │  │          │  │          │  │        │  │
└────────────────┘   │  │PyMuPDF   │  │Dense+BM25│  │Ollama  │  │   ┌──────────────┐
                     │  │Chunker   │  │RRF+Rerank│  │LLM     │──┼──▶│    Ollama    │
                     │  └──────────┘  └──────────┘  └────────┘  │   │  llama3.1:8b │
                     └──────────────────────────────────────────┘   └──────────────┘
```

### The 4 Pipelines

1. **Ingestion** (`backend/app/ingestion/`) — parse → chunk → embed → store
2. **Retrieval** (`backend/app/retrieval/`) — dense search + sparse search → RRF fusion → cross-encoder re-rank
3. **Generation** (`backend/app/generation/`) — retrieve → prompt → LLM call → citation parse → persist
4. **Evaluation** (`evaluation/`) — upload papers → run queries → compute metrics

---

## Tech Stack

### Backend
- **FastAPI** — async Python web framework
- **SQLAlchemy 2.0** + **asyncpg** — async ORM and PostgreSQL driver
- **Alembic** — schema migrations
- **PyMuPDF** — PDF parsing with font-size/bold classification
- **sentence-transformers** — `all-MiniLM-L6-v2` (384-dim embeddings) + `ms-marco-MiniLM-L-6-v2` (cross-encoder)
- **tiktoken** — token counting for chunking
- **pgvector** — Postgres vector extension for dense search

### Frontend
- **Next.js 15** (App Router) + **React 19** + **TypeScript**
- **Tailwind CSS 4** — styling
- **pdfjs-dist** — PDF rendering in-browser

### Infrastructure
- **PostgreSQL 16** with pgvector extension
- **Ollama** — local LLM inference (GPU-accelerated)
- **Docker Compose** — orchestrates all four services

---

## Prerequisites

- **Docker Desktop** (with GPU support enabled for Ollama)
- **32GB RAM** recommended (Ollama + PostgreSQL + app services)
- **NVIDIA GPU** (optional but strongly recommended for LLM inference speed)
- Python 3.11+ (only if running the backend outside Docker)
- Node.js 20+ (only if running the frontend outside Docker)

---

## Quick Start

### 1. Clone and configure
```bash
git clone <your-repo-url>
cd RAG
cp .env.example .env
```

### 2. Launch everything with Docker
```bash
docker compose up
```

This starts four services:
- `db` — PostgreSQL with pgvector on port **5432**
- `ollama` — Ollama server on port **11434**
- `backend` — FastAPI on port **8000** (runs Alembic migrations on startup)
- `frontend` — Next.js on port **3000**

### 3. Pull the Ollama model (first run only)
```bash
bash scripts/pull_model.sh
# Or manually:
docker compose exec ollama ollama pull llama3.1:8b
```

### 4. Open the app
Navigate to **http://localhost:3000**

---

## Usage

1. **Upload a paper** — Drag a PDF onto the upload zone on the home page. The paper goes into `processing` status while chunks are extracted, embedded, and indexed.
2. **Wait for ready** — The page auto-polls every 5 seconds. When status turns `ready`, click **Ask Questions**.
3. **Ask a question** — Type in the chat panel, e.g. *"What is the main contribution of this paper?"*
4. **Click citations** — Every `[N]` reference in the answer is clickable. Clicking scrolls the PDF viewer to the cited page and shows the section heading.

---

## API Reference

Base URL: `http://localhost:8000/api`

| Method | Endpoint                      | Description                            |
|--------|-------------------------------|----------------------------------------|
| POST   | `/papers`                     | Upload a PDF (multipart form)          |
| GET    | `/papers`                     | List papers (filter by `?status=ready`)|
| GET    | `/papers/{id}`                | Get paper details + chunk count        |
| GET    | `/papers/{id}/pdf`            | Stream the raw PDF                     |
| GET    | `/papers/{id}/chunks`         | List chunks (filter by `?page=N`)      |
| POST   | `/query`                      | Ask a question — returns answer + citations |
| GET    | `/conversations`              | List conversations                     |
| GET    | `/conversations/{id}`         | Full conversation with messages        |
| GET    | `/health`                     | Health check                           |

**Query request example:**
```json
POST /api/query
{
  "paper_id": "uuid-here",
  "question": "What is multi-head attention?",
  "conversation_id": null,
  "top_k": 10,
  "rerank_top_n": 5,
  "llm_provider": "ollama"
}
```

**Response:**
```json
{
  "conversation_id": "...",
  "message_id": "...",
  "answer": "Multi-head attention projects queries, keys, and values h times [1]...",
  "citations": [
    {
      "chunk_id": "...",
      "chunk_index": 14,
      "page_number": 5,
      "section_heading": "3.2.2 Multi-Head Attention",
      "snippet": "Instead of performing a single attention function..."
    }
  ]
}
```

---

## Project Structure

```
RAG/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/              # Route handlers (papers, query, conversations)
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── ingestion/        # PDF parser, chunker, ingestion pipeline
│   │   ├── retrieval/        # Embedder, dense, sparse, fusion, reranker
│   │   ├── generation/       # LLM client, prompts, generation pipeline
│   │   ├── db/               # Async SQLAlchemy session
│   │   ├── config.py         # Pydantic settings
│   │   └── main.py           # FastAPI app with lifespan
│   ├── alembic/              # Database migrations
│   └── tests/                # Pytest test suite (52 tests)
│
├── frontend/                 # Next.js frontend
│   └── src/
│       ├── app/              # App Router pages
│       │   ├── page.tsx              # Home: upload + paper list
│       │   └── papers/[id]/page.tsx  # Detail: split PDF/chat view
│       ├── components/       # React components
│       │   ├── PdfViewer.tsx
│       │   ├── ChatPanel.tsx
│       │   ├── MessageBubble.tsx
│       │   ├── CitationTag.tsx
│       │   ├── PaperUpload.tsx
│       │   └── PaperList.tsx
│       └── lib/              # API client + TypeScript types
│
├── evaluation/               # Evaluation harness
│   ├── qa_pairs.json         # Ground-truth QA pairs
│   ├── eval_runner.py        # Runs queries and collects results
│   ├── metrics.py            # Recall@k, citation precision/recall
│   └── papers/               # Sample PDFs
│
├── scripts/                  # Helper scripts
│   ├── pull_model.sh
│   └── run_eval.sh
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Testing

The backend has 52 unit tests covering chunker, parser, RRF fusion, citation parsing, and evaluation metrics.

```bash
cd backend
pip install -e ".[dev]"
python -m pytest tests/ -v
```

Expected output:
```
52 passed in ~8s
```

### What's tested

| Component            | Tests                                                              |
|----------------------|--------------------------------------------------------------------|
| Token counter        | Empty, simple, long text                                           |
| Semantic chunker     | Section boundaries, table/figure isolation, token overflow splits, overlap, chunk indices, page tracking |
| Element classifier   | Figure/table captions, bold titles, large-font titles, body text  |
| Title/author extractor | Basic extraction, no-authors fallback, page-1 scope              |
| RRF fusion           | Single/multiple lists, score formula, empty edge cases             |
| Citation parser      | Single, multiple, duplicate, out-of-range, ordering, zero-index    |
| Evaluation metrics   | Recall@k at various k, precision, recall, empty samples            |

---

## Evaluation

The evaluation harness measures three metric families against ground-truth QA pairs in `evaluation/qa_pairs.json`.

```bash
# With docker compose up running:
cd evaluation
python eval_runner.py
```

### Metrics

| Metric                | What it measures                                                     | Target |
|-----------------------|----------------------------------------------------------------------|--------|
| **Retrieval Recall@5**  | % of ground-truth chunks found in top-5 retrieved chunks           | > 0.7  |
| **Retrieval Recall@10** | % of ground-truth chunks found in top-10 retrieved chunks          | > 0.85 |
| **Citation Precision**  | % of cited chunks that are in ground truth                         | > 0.8  |
| **Citation Recall**     | % of ground-truth chunks that were cited in the answer             | > 0.6  |

Add your own PDFs to `evaluation/papers/` and ground-truth QA pairs to `evaluation/qa_pairs.json`.

---

## Configuration

All settings live in `.env` (copy from `.env.example`):

| Variable             | Default                                  | Description                       |
|----------------------|------------------------------------------|-----------------------------------|
| `DATABASE_URL`       | `postgresql+asyncpg://rag:rag@db:5432/rag` | PostgreSQL connection           |
| `OLLAMA_BASE_URL`    | `http://ollama:11434`                    | Ollama API endpoint               |
| `OLLAMA_MODEL`       | `llama3.1:8b`                            | Ollama model to use               |
| `EMBEDDING_MODEL`    | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model (384 dims)        |
| `RERANKER_MODEL`     | `cross-encoder/ms-marco-MiniLM-L-6-v2`   | Cross-encoder for re-ranking      |
| `ANTHROPIC_API_KEY`  | (empty)                                  | Optional: enables Anthropic provider |
| `OPENAI_API_KEY`     | (empty)                                  | Optional: enables OpenAI provider |

---

## Design Decisions

- **BM25 via PostgreSQL `tsvector`** instead of Elasticsearch — keeps the stack lean. For a single-paper query scope, the GIN-indexed tsvector is fast enough.
- **Background ingestion via FastAPI `BackgroundTasks`** — simpler than Celery for v1. No retry semantics; swap to `arq`/Celery if ingestion becomes unreliable.
- **Cross-encoder re-ranker after RRF** — RRF merges two signal types (semantic + keyword); the cross-encoder adds token-level query-document interaction on the top candidates for best quality/latency tradeoff.
- **`[N]`-indexed citations** — simpler than embedding chunk UUIDs in LLM output. The frontend maps `[1]` → `citations[0]`.
- **PDF served by backend** — `FileResponse` is fine for dev; front with nginx or S3 pre-signed URLs for production.

---

## Troubleshooting

### Docker errors
- **"cannot connect to Docker daemon"** — Docker Desktop isn't running. Open it from the Start menu and wait for "Docker Desktop is running".
- **Ollama slow on first run** — Model downloads are one-time but large (~5GB for `llama3.1:8b`).
- **GPU not used by Ollama** — Ensure NVIDIA Container Toolkit is installed and Docker Desktop has GPU support enabled.

### Ingestion stuck on "processing"
Check backend logs: `docker compose logs -f backend`. Large PDFs can take several minutes — most of the time is spent downloading embedding models on the first run.

### Empty retrieval results
Ensure `status = 'ready'` for the paper and chunks exist: `GET /api/papers/{id}/chunks`.

---

## License

MIT
