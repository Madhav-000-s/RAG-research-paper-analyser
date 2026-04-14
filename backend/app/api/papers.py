import os
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models.paper import Chunk, Paper
from app.schemas.paper import ChunkResponse, PaperDetailResponse, PaperResponse

router = APIRouter()


@router.post("", response_model=PaperResponse, status_code=201)
async def upload_paper(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Save the PDF to storage
    paper_id = uuid.uuid4()
    pdf_dir = Path(settings.pdf_storage_dir)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{paper_id}.pdf"

    content = await file.read()
    with open(pdf_path, "wb") as f:
        f.write(content)

    # Create paper record
    paper = Paper(
        id=paper_id,
        filename=file.filename,
        status="processing",
        pdf_path=str(pdf_path),
    )
    db.add(paper)
    await db.flush()

    # Kick off ingestion in background
    from app.ingestion.pipeline import ingest_paper

    background_tasks.add_task(ingest_paper, paper_id, str(pdf_path))

    return paper


@router.get("", response_model=list[PaperResponse])
async def list_papers(
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(Paper).order_by(Paper.created_at.desc())
    if status:
        query = query.where(Paper.status == status)
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{paper_id}", response_model=PaperDetailResponse)
async def get_paper(paper_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get chunk count
    count_result = await db.execute(
        select(func.count()).where(Chunk.paper_id == paper_id)
    )
    chunk_count = count_result.scalar() or 0

    return PaperDetailResponse(
        id=paper.id,
        filename=paper.filename,
        title=paper.title,
        authors=paper.authors,
        page_count=paper.page_count,
        status=paper.status,
        created_at=paper.created_at,
        chunk_count=chunk_count,
    )


@router.get("/{paper_id}/pdf")
async def get_paper_pdf(paper_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if not os.path.exists(paper.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    return FileResponse(
        paper.pdf_path,
        media_type="application/pdf",
        filename=paper.filename,
    )


@router.get("/{paper_id}/chunks", response_model=list[ChunkResponse])
async def get_paper_chunks(
    paper_id: uuid.UUID,
    page: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Chunk)
        .where(Chunk.paper_id == paper_id)
        .order_by(Chunk.chunk_index)
    )
    if page is not None:
        query = query.where(Chunk.page_number == page)
    result = await db.execute(query)
    return result.scalars().all()
