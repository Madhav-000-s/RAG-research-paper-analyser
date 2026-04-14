"""Ingestion pipeline: parse -> chunk -> embed -> store."""

import logging
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.ingestion.chunker import semantic_chunk
from app.ingestion.parser import extract_title_and_authors, parse_pdf
from app.models.paper import Chunk as ChunkModel
from app.models.paper import Paper

logger = logging.getLogger(__name__)


async def ingest_paper(paper_id: uuid.UUID, pdf_path: str) -> None:
    """
    Full ingestion pipeline. Runs as a background task.
    Creates its own DB session since background tasks don't share
    the request's session.
    """
    # Create a fresh engine/session for background task
    engine = create_async_engine(settings.database_url, pool_size=5)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        try:
            logger.info(f"Starting ingestion for paper {paper_id}")

            # Step 1: Parse PDF
            elements, page_count = parse_pdf(pdf_path)
            logger.info(f"Parsed {len(elements)} elements from {page_count} pages")

            # Extract metadata
            title, authors = extract_title_and_authors(elements)

            # Step 2: Chunk
            chunks = semantic_chunk(
                elements,
                max_tokens=settings.chunk_size_tokens,
                overlap_tokens=settings.chunk_overlap_tokens,
            )
            logger.info(f"Created {len(chunks)} chunks")

            # Step 3: Embed
            from app.retrieval.embedder import Embedder

            embedder = Embedder(settings.embedding_model)
            texts = [c.content for c in chunks]
            embeddings = embedder.encode(texts) if texts else []

            # Step 4: Store chunks
            chunk_models = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_models.append(
                    ChunkModel(
                        paper_id=paper_id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        chunk_type=chunk.chunk_type,
                        page_number=chunk.page_number,
                        section_heading=chunk.section_heading,
                        token_count=chunk.token_count,
                        embedding=embedding.tolist(),
                        metadata_={},
                    )
                )

            db.add_all(chunk_models)

            # Step 5: Update paper status
            await db.execute(
                update(Paper)
                .where(Paper.id == paper_id)
                .values(
                    status="ready",
                    title=title,
                    authors=authors if authors else None,
                    page_count=page_count,
                )
            )
            await db.commit()
            logger.info(f"Paper {paper_id} ingestion complete: {len(chunks)} chunks stored")

        except Exception as e:
            logger.error(f"Ingestion failed for paper {paper_id}: {e}")
            await db.execute(
                update(Paper)
                .where(Paper.id == paper_id)
                .values(status="error")
            )
            await db.commit()
            raise
        finally:
            await engine.dispose()
