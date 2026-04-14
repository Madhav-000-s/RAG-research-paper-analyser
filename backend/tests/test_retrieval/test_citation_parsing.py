"""Tests for citation parsing from LLM output."""

import uuid

import pytest

from app.generation.pipeline import parse_citations
from app.retrieval.dense import ScoredChunk


def _make_chunk(index: int) -> ScoredChunk:
    return ScoredChunk(
        id=uuid.uuid5(uuid.NAMESPACE_DNS, f"chunk-{index}"),
        chunk_index=index,
        content=f"Content for chunk {index}. " * 20,
        page_number=index + 1,
        section_heading=f"Section {index}",
        score=0.9,
    )


class TestParseCitations:
    def test_single_citation(self):
        chunks = [_make_chunk(0), _make_chunk(1)]
        answer = "The method works well [1]."
        citations = parse_citations(answer, chunks)
        assert len(citations) == 1
        assert citations[0].chunk_index == 0
        assert citations[0].page_number == 1

    def test_multiple_citations(self):
        chunks = [_make_chunk(0), _make_chunk(1), _make_chunk(2)]
        answer = "Claim A [1]. Claim B [2][3]."
        citations = parse_citations(answer, chunks)
        assert len(citations) == 3

    def test_duplicate_citations_deduplicated(self):
        chunks = [_make_chunk(0)]
        answer = "First mention [1]. Second mention [1]."
        citations = parse_citations(answer, chunks)
        assert len(citations) == 1

    def test_out_of_range_citation_ignored(self):
        chunks = [_make_chunk(0)]
        answer = "Valid [1]. Invalid [5]."
        citations = parse_citations(answer, chunks)
        assert len(citations) == 1

    def test_no_citations(self):
        chunks = [_make_chunk(0)]
        answer = "An answer with no citations."
        citations = parse_citations(answer, chunks)
        assert len(citations) == 0

    def test_citation_snippet_truncated(self):
        chunks = [_make_chunk(0)]
        answer = "See [1]."
        citations = parse_citations(answer, chunks)
        assert len(citations[0].snippet) <= 200

    def test_citation_ordering(self):
        chunks = [_make_chunk(0), _make_chunk(1), _make_chunk(2)]
        answer = "Last [3], first [1], middle [2]."
        citations = parse_citations(answer, chunks)
        # Should be ordered by citation number
        assert citations[0].chunk_index == 0
        assert citations[1].chunk_index == 1
        assert citations[2].chunk_index == 2

    def test_zero_citation_ignored(self):
        chunks = [_make_chunk(0)]
        answer = "Invalid [0]. Valid [1]."
        citations = parse_citations(answer, chunks)
        assert len(citations) == 1
        assert citations[0].chunk_index == 0
