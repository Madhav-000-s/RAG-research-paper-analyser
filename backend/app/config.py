from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://rag:rag@localhost:5432/rag"

    # Storage
    pdf_storage_dir: str = "./storage/pdfs"

    # Embedding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # Chunking
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 50

    # Reranker
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Ollama (primary LLM)
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1:8b"

    # Anthropic (optional)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # OpenAI (optional)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Retrieval
    rrf_k: int = 60
    default_top_k: int = 20
    default_rerank_top_n: int = 5

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
