from fastapi import APIRouter

from app.api.papers import router as papers_router
from app.api.query import router as query_router
from app.api.conversations import router as conversations_router

api_router = APIRouter()
api_router.include_router(papers_router, prefix="/papers", tags=["papers"])
api_router.include_router(query_router, prefix="/query", tags=["query"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
