"""Initial schema with papers, chunks, conversations, messages.

Revision ID: 001
Revises:
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Papers table
    op.create_table(
        "papers",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("title", sa.Text()),
        sa.Column("authors", sa.ARRAY(sa.String())),
        sa.Column("page_count", sa.Integer()),
        sa.Column("status", sa.String(20), nullable=False, server_default="processing"),
        sa.Column("pdf_path", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Chunks table
    op.create_table(
        "chunks",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("paper_id", sa.UUID(), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_type", sa.String(20), nullable=False, server_default="text"),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("section_heading", sa.Text()),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("metadata", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("idx_chunks_paper_id", "chunks", ["paper_id"])
    op.execute("""
        CREATE INDEX idx_chunks_embedding ON chunks
        USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
    """)
    op.execute("""
        CREATE INDEX idx_chunks_tsvector ON chunks
        USING GIN (to_tsvector('english', content))
    """)

    # Conversations table
    op.create_table(
        "conversations",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("paper_id", sa.UUID(), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Messages table
    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", sa.UUID(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("idx_messages_conversation", "messages", ["conversation_id", "created_at"])


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("chunks")
    op.drop_table("papers")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS vector")
