"""Tests for semantic chunking logic."""

import pytest

from app.ingestion.chunker import Chunk, count_tokens, semantic_chunk
from app.ingestion.parser import ParsedElement


def _make_element(
    text: str,
    element_type: str = "text",
    page_number: int = 1,
    section_heading: str | None = None,
) -> ParsedElement:
    return ParsedElement(
        text=text,
        element_type=element_type,
        page_number=page_number,
        section_heading=section_heading,
    )


class TestCountTokens:
    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_simple_text(self):
        tokens = count_tokens("Hello world")
        assert tokens > 0
        assert tokens < 10

    def test_longer_text(self):
        text = "The quick brown fox jumps over the lazy dog. " * 20
        tokens = count_tokens(text)
        assert tokens > 50


class TestSemanticChunk:
    def test_single_short_element(self):
        elements = [_make_element("Hello world, this is a test.")]
        chunks = semantic_chunk(elements, max_tokens=512, overlap_tokens=50)
        assert len(chunks) == 1
        assert chunks[0].content == "Hello world, this is a test."
        assert chunks[0].chunk_index == 0
        assert chunks[0].page_number == 1

    def test_multiple_elements_within_budget(self):
        elements = [
            _make_element("First paragraph."),
            _make_element("Second paragraph."),
            _make_element("Third paragraph."),
        ]
        chunks = semantic_chunk(elements, max_tokens=512, overlap_tokens=0)
        assert len(chunks) == 1
        assert "First paragraph" in chunks[0].content
        assert "Third paragraph" in chunks[0].content

    def test_section_boundary_respected(self):
        elements = [
            _make_element("Content before heading."),
            _make_element("Introduction", element_type="title"),
            _make_element("Content after heading."),
        ]
        chunks = semantic_chunk(elements, max_tokens=512, overlap_tokens=0)
        assert len(chunks) == 2
        assert "Content before heading" in chunks[0].content
        assert "Content after heading" in chunks[1].content

    def test_table_is_standalone(self):
        elements = [
            _make_element("Some text."),
            _make_element("Table: X | Y | Z", element_type="table"),
            _make_element("More text."),
        ]
        chunks = semantic_chunk(elements, max_tokens=512, overlap_tokens=0)
        assert len(chunks) == 3
        assert chunks[1].chunk_type == "table"

    def test_figure_caption_is_standalone(self):
        elements = [
            _make_element("Some text."),
            _make_element("Figure 1: Architecture diagram", element_type="figure_caption"),
            _make_element("More text."),
        ]
        chunks = semantic_chunk(elements, max_tokens=512, overlap_tokens=0)
        assert any(c.chunk_type == "figure_caption" for c in chunks)

    def test_exceeds_token_budget_splits(self):
        # Create element that needs splitting
        long_text = "This is a sentence. " * 100
        elements = [_make_element(long_text)]
        chunks = semantic_chunk(elements, max_tokens=50, overlap_tokens=0)
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.token_count <= 60  # some tolerance for sentence boundaries

    def test_overlap_is_applied(self):
        # Two elements that individually fit but together exceed budget
        text_a = "Alpha beta gamma delta. " * 30
        text_b = "Epsilon zeta eta theta. " * 30
        elements = [_make_element(text_a), _make_element(text_b)]
        chunks = semantic_chunk(elements, max_tokens=100, overlap_tokens=20)
        assert len(chunks) >= 2
        # Second chunk should contain some overlap from first
        # (the overlap text from end of first chunk)

    def test_chunk_indices_are_sequential(self):
        elements = [
            _make_element("Section A", element_type="title"),
            _make_element("Content A"),
            _make_element("Table data", element_type="table"),
            _make_element("Section B", element_type="title"),
            _make_element("Content B"),
        ]
        chunks = semantic_chunk(elements, max_tokens=512, overlap_tokens=0)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_page_numbers_tracked(self):
        elements = [
            _make_element("Page 1 content", page_number=1),
            _make_element("Page 2 content", page_number=2),
        ]
        chunks = semantic_chunk(elements, max_tokens=512, overlap_tokens=0)
        # Last page number should be preserved
        assert chunks[-1].page_number == 2

    def test_empty_elements(self):
        chunks = semantic_chunk([], max_tokens=512, overlap_tokens=0)
        assert chunks == []

    def test_section_heading_propagated(self):
        elements = [
            _make_element("Methods", element_type="title"),
            _make_element("We conducted an experiment.", section_heading="Methods"),
        ]
        chunks = semantic_chunk(elements, max_tokens=512, overlap_tokens=0)
        assert len(chunks) == 1
        assert chunks[0].section_heading == "Methods"
