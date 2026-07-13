"""Format parsers: bytes -> structured blocks (DESIGN.md Section 9.1).

Every parser produces the same shape — a list of Blocks carrying the heading
path they sit under — so the chunker can stay structure-aware without caring
about the source format. Supported formats are bounded by Section 3.2.
"""

import io
import re
from dataclasses import dataclass


@dataclass
class Block:
    headings: list[str]  # e.g. ["Section 2", "2.1 Overview"]
    text: str


def parse(mime_type: str, content: bytes) -> list[Block]:
    parser = _PARSERS.get(mime_type)
    if parser is None:
        raise ValueError(f"no parser for mime type {mime_type}")
    return [b for b in parser(content) if b.text.strip()]


def _parse_markdown(content: bytes) -> list[Block]:
    blocks: list[Block] = []
    headings: dict[int, str] = {}
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            path = [headings[level] for level in sorted(headings)]
            blocks.append(Block(headings=path, text=" ".join(paragraph)))
            paragraph.clear()

    for line in content.decode("utf-8", errors="replace").splitlines():
        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if match:
            flush()
            level = len(match.group(1))
            headings[level] = match.group(2).strip()
            # a new heading invalidates deeper levels
            for deeper in [lvl for lvl in headings if lvl > level]:
                del headings[deeper]
        elif line.strip():
            paragraph.append(line.strip())
        else:
            flush()
    flush()
    return blocks


def _parse_html(content: bytes) -> list[Block]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(content, "html.parser")
    blocks: list[Block] = []
    headings: dict[int, str] = {}
    for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
        text = element.get_text(" ", strip=True)
        if not text:
            continue
        if element.name.startswith("h"):
            level = int(element.name[1])
            headings[level] = text
            for deeper in [lvl for lvl in headings if lvl > level]:
                del headings[deeper]
        else:
            path = [headings[level] for level in sorted(headings)]
            blocks.append(Block(headings=path, text=text))
    return blocks


def _parse_text(content: bytes) -> list[Block]:
    text = content.decode("utf-8", errors="replace")
    return [
        Block(headings=[], text=re.sub(r"\s+", " ", paragraph).strip())
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]


def _parse_pdf(content: bytes) -> list[Block]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    blocks: list[Block] = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        for paragraph in re.split(r"\n\s*\n", page_text):
            cleaned = re.sub(r"\s+", " ", paragraph).strip()
            if cleaned:
                blocks.append(Block(headings=[f"Page {page_number}"], text=cleaned))
    return blocks


def _parse_docx(content: bytes) -> list[Block]:
    import docx

    document = docx.Document(io.BytesIO(content))
    blocks: list[Block] = []
    headings: dict[int, str] = {}
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        style = (paragraph.style.name or "") if paragraph.style else ""
        match = re.match(r"^Heading (\d)$", style)
        if match:
            level = int(match.group(1))
            headings[level] = text
            for deeper in [lvl for lvl in headings if lvl > level]:
                del headings[deeper]
        else:
            path = [headings[level] for level in sorted(headings)]
            blocks.append(Block(headings=path, text=text))
    return blocks


_PARSERS = {
    "text/markdown": _parse_markdown,
    "text/html": _parse_html,
    "text/plain": _parse_text,
    "application/pdf": _parse_pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": _parse_docx,
}
