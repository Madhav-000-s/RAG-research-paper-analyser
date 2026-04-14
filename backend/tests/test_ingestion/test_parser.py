"""Tests for PDF parser element classification."""

import pytest

from app.ingestion.parser import _classify_element, extract_title_and_authors, ParsedElement


class TestClassifyElement:
    def test_figure_caption(self):
        assert _classify_element("Figure 1: Architecture", 10.0, False, 0) == "figure_caption"
        assert _classify_element("Fig. 2 shows the results", 10.0, False, 0) == "figure_caption"

    def test_table_caption(self):
        assert _classify_element("Table 1: Results", 10.0, False, 0) == "table"

    def test_bold_short_text_is_title(self):
        assert _classify_element("Introduction", 12.0, True, 0) == "title"

    def test_large_font_short_text_is_title(self):
        assert _classify_element("Abstract", 14.0, False, 0) == "title"

    def test_regular_text(self):
        long_text = "This is a regular paragraph of text that describes the methodology used in our experiment."
        assert _classify_element(long_text, 10.0, False, 0) == "text"

    def test_long_bold_text_is_text(self):
        long_text = "A" * 250
        assert _classify_element(long_text, 10.0, True, 0) == "text"


class TestExtractTitleAndAuthors:
    def test_basic_extraction(self):
        elements = [
            ParsedElement("Deep Learning for NLP", "title", 1),
            ParsedElement("John Smith, Jane Doe, and Bob Wilson", "text", 1),
        ]
        title, authors = extract_title_and_authors(elements)
        assert title == "Deep Learning for NLP"
        assert len(authors) == 3
        assert "John Smith" in authors

    def test_no_authors(self):
        elements = [
            ParsedElement("A Paper Title", "title", 1),
            ParsedElement("This is the abstract of the paper.", "text", 1),
        ]
        title, authors = extract_title_and_authors(elements)
        assert title == "A Paper Title"
        assert authors == []

    def test_empty_elements(self):
        title, authors = extract_title_and_authors([])
        assert title is None
        assert authors == []

    def test_only_page_one_considered(self):
        elements = [
            ParsedElement("Main Title", "title", 1),
            ParsedElement("Author One, Author Two", "text", 1),
            ParsedElement("Another Title", "title", 2),  # Page 2 — ignored
        ]
        title, authors = extract_title_and_authors(elements)
        assert title == "Main Title"
        assert len(authors) == 2
