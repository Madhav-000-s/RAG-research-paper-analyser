from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML models into app.state at startup, clean up on shutdown."""
    # Lazy imports to avoid loading heavy ML libs at import time
    from app.retrieval.embedder import Embedder
    from app.retrieval.reranker import Reranker
    from app.generation.llm import LLMClient

    app.state.embedder = Embedder(settings.embedding_model)
    app.state.reranker = Reranker(settings.reranker_model)
    app.state.llm = LLMClient(settings)
    yield


app = FastAPI(
    title="RAG Paper Intelligence",
    description="Research Paper Intelligence Engine with hybrid retrieval and citations",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from app.api.router import api_router  # noqa: E402

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
