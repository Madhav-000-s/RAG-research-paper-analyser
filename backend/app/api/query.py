from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.paper import Paper
from app.schemas.query import QueryRequest, QueryResponse

router = APIRouter()


@router.post("", response_model=QueryResponse)
async def ask_question(
    request_body: QueryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Verify paper exists and is ready
    result = await db.execute(
        select(Paper).where(Paper.id == request_body.paper_id)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    if paper.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Paper is not ready for queries (status: {paper.status})",
        )

    from app.generation.pipeline import answer_question

    response = await answer_question(
        request=request_body,
        db=db,
        embedder=request.app.state.embedder,
        reranker=request.app.state.reranker,
        llm=request.app.state.llm,
    )
    return response
