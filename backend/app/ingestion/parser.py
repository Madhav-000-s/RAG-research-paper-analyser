"""PDF parsing using PyMuPDF with metadata extraction."""

from dataclasses import dataclass, field

import fitz  # PyMuPDF


@dataclass
class ParsedElement:
    text: str
    element_type: str  # "title", "text", "table", "figure_caption"
    page_number: int
    section_heading: str | None = None
    bbox: dict = field(default_factory=dict)  # {x0, y0, x1, y1}


def parse_pdf(pdf_path: str) -> tuple[list[ParsedElement], int]:
    """
    Parse a PDF into structured elements using PyMuPDF.

    Returns:
        Tuple of (elements, page_count)
    """
    doc = fitz.open(pdf_path)
    page_count = len(doc)
    elements: list[ParsedElement] = []
    current_section: str | None = None

    for page_num in range(page_count):
        page = doc[page_num]
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

        for block in blocks:
            if block["type"] != 0:  # Skip image blocks
                continue

            block_text = ""
            max_font_size = 0.0
            is_bold = False

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    block_text += span["text"]
                    if span["size"] > max_font_size:
                        max_font_size = span["size"]
                    if "bold" in span.get("font", "").lower():
                        is_bold = True
                block_text += "\n"

            block_text = block_text.strip()
            if not block_text or len(block_text) < 3:
                continue

            # Classify element type based on font properties
            element_type = _classify_element(
                block_text, max_font_size, is_bold, page_num
            )

            # Track section headings
            if element_type == "title":
                current_section = block_text

            bbox = {
                "x0": block["bbox"][0],
                "y0": block["bbox"][1],
                "x1": block["bbox"][2],
                "y1": block["bbox"][3],
            }

            elements.append(
                ParsedElement(
                    text=block_text,
                    element_type=element_type,
                    page_number=page_num + 1,  # 1-indexed
                    section_heading=current_section,
                    bbox=bbox,
                )
            )

    doc.close()
    return elements, page_count


def _classify_element(
    text: str, font_size: float, is_bold: bool, page_num: int
) -> str:
    """Classify a text block as title, text, table, or figure_caption."""
    text_lower = text.lower().strip()

    # Figure captions
    if text_lower.startswith(("figure ", "fig.", "fig ")):
        return "figure_caption"

    # Table captions
    if text_lower.startswith(("table ",)):
        return "table"

    # Section headings: bold text with larger font or short bold lines
    if is_bold and len(text) < 200:
        return "title"

    if font_size > 12 and len(text) < 200:
        return "title"

    return "text"


def extract_title_and_authors(elements: list[ParsedElement]) -> tuple[str | None, list[str]]:
    """Extract paper title and authors from the first page elements."""
    title = None
    authors: list[str] = []

    # Title is usually the first large text element on page 1
    page_one = [e for e in elements if e.page_number == 1]
    for i, elem in enumerate(page_one):
        if elem.element_type == "title" and title is None:
            title = elem.text
        elif title and elem.element_type == "text" and not authors:
            # The text right after the title is often the author list
            potential_authors = elem.text
            # Simple heuristic: if it contains commas or "and", treat as authors
            if "," in potential_authors or " and " in potential_authors.lower():
                authors = [a.strip() for a in potential_authors.replace(" and ", ",").split(",")]
                authors = [a for a in authors if a and len(a) < 100]
            break

    return title, authors
