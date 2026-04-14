"""Semantic chunking with section-boundary respect and token budget."""

from dataclasses import dataclass

import tiktoken

from app.ingestion.parser import ParsedElement


@dataclass
class Chunk:
    content: str
    chunk_type: str
    page_number: int
    section_heading: str | None
    token_count: int
    chunk_index: int = 0


# Use cl100k_base encoder (GPT-4 / modern models)
_encoder = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_encoder.encode(text))


def semantic_chunk(
    elements: list[ParsedElement],
    max_tokens: int = 512,
    overlap_tokens: int = 50,
) -> list[Chunk]:
    """
    Group ParsedElements into chunks respecting:
    1. Section boundaries — never merge across section headings
    2. Token budget — each chunk <= max_tokens
    3. Overlap — last overlap_tokens of chunk N prepended to chunk N+1
    4. Element type — tables and figure captions are standalone chunks
    """
    chunks: list[Chunk] = []
    current_texts: list[str] = []
    current_tokens = 0
    current_section: str | None = None
    current_page: int = 1
    overlap_text = ""

    def _flush():
        nonlocal current_texts, current_tokens, overlap_text
        if not current_texts:
            return
        content = "\n".join(current_texts).strip()
        if not content:
            current_texts = []
            current_tokens = 0
            return

        token_count = count_tokens(content)
        chunks.append(
            Chunk(
                content=content,
                chunk_type="text",
                page_number=current_page,
                section_heading=current_section,
                token_count=token_count,
            )
        )

        # Compute overlap: take text from the end of current content
        if overlap_tokens > 0:
            tokens = _encoder.encode(content)
            overlap_token_ids = tokens[-overlap_tokens:]
            overlap_text = _encoder.decode(overlap_token_ids)
        else:
            overlap_text = ""

        current_texts = []
        current_tokens = 0

    for elem in elements:
        # Tables and figure captions are always standalone
        if elem.element_type in ("table", "figure_caption"):
            _flush()
            token_count = count_tokens(elem.text)
            chunks.append(
                Chunk(
                    content=elem.text,
                    chunk_type=elem.element_type,
                    page_number=elem.page_number,
                    section_heading=elem.section_heading,
                    token_count=token_count,
                )
            )
            overlap_text = ""
            continue

        # Section heading — flush current buffer, start new section
        if elem.element_type == "title":
            _flush()
            current_section = elem.text
            current_page = elem.page_number
            # Don't add overlap from previous section
            overlap_text = ""
            continue

        # Regular text element
        elem_tokens = count_tokens(elem.text)

        # If adding this element would exceed budget, flush first
        if current_tokens + elem_tokens > max_tokens and current_texts:
            _flush()
            # Prepend overlap from previous chunk
            if overlap_text:
                current_texts.append(overlap_text)
                current_tokens = count_tokens(overlap_text)
                overlap_text = ""

        # If a single element exceeds max_tokens, split it by sentences
        if elem_tokens > max_tokens:
            _flush()
            sub_chunks = _split_long_text(
                elem.text, max_tokens, overlap_tokens, elem.page_number,
                elem.section_heading or current_section,
            )
            chunks.extend(sub_chunks)
            continue

        if not current_texts:
            current_page = elem.page_number
            if overlap_text:
                current_texts.append(overlap_text)
                current_tokens = count_tokens(overlap_text)
                overlap_text = ""

        current_texts.append(elem.text)
        current_tokens += elem_tokens
        current_page = elem.page_number

    _flush()

    # Assign sequential chunk indices
    for i, chunk in enumerate(chunks):
        chunk.chunk_index = i

    return chunks


def _split_long_text(
    text: str,
    max_tokens: int,
    overlap_tokens: int,
    page_number: int,
    section_heading: str | None,
) -> list[Chunk]:
    """Split a long text block into smaller chunks by sentence boundaries."""
    # Split on sentence boundaries
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[Chunk] = []
    current: list[str] = []
    current_count = 0

    for sentence in sentences:
        s_tokens = count_tokens(sentence)
        if current_count + s_tokens > max_tokens and current:
            content = " ".join(current)
            chunks.append(
                Chunk(
                    content=content,
                    chunk_type="text",
                    page_number=page_number,
                    section_heading=section_heading,
                    token_count=count_tokens(content),
                )
            )
            # Keep last sentence as overlap approximation
            if overlap_tokens > 0 and current:
                current = [current[-1]]
                current_count = count_tokens(current[0])
            else:
                current = []
                current_count = 0

        current.append(sentence)
        current_count += s_tokens

    if current:
        content = " ".join(current)
        chunks.append(
            Chunk(
                content=content,
                chunk_type="text",
                page_number=page_number,
                section_heading=section_heading,
                token_count=count_tokens(content),
            )
        )

    return chunks
