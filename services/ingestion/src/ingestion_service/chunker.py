"""Structure-aware chunking (ARCHITECTURE.md Section 9.1).

Chunks never cross a heading boundary; within a section, paragraphs
accumulate to a target token budget with one paragraph of overlap carried
between adjacent chunks. Token counts are estimated at ~4 characters per
token — good enough for budgeting without a tokenizer dependency.
"""

from dataclasses import dataclass

from ingestion_service.parsers import Block

TARGET_TOKENS = 450  # inside the spec's ~400–800 window
MAX_TOKENS = 800


@dataclass
class Chunk:
    ordinal: int
    text: str
    headings: list[str]
    token_count: int


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def chunk(blocks: list[Block]) -> list[Chunk]:
    chunks: list[Chunk] = []
    section: list[str] | None = None
    buffer: list[str] = []
    # True while the buffer holds nothing beyond the overlap paragraph carried
    # from the previous chunk — flushing then would emit duplicate content.
    carried_only = False

    def emit(carry_overlap: bool) -> None:
        nonlocal buffer, carried_only
        if not buffer or (carried_only and not carry_overlap):
            buffer = []
            carried_only = False
            return
        heading_prefix = " › ".join(section) if section else ""
        body = " ".join(buffer)
        text = f"{heading_prefix}\n{body}" if heading_prefix else body
        chunks.append(
            Chunk(
                ordinal=len(chunks),
                text=text,
                headings=list(section or []),
                token_count=estimate_tokens(text),
            )
        )
        if carry_overlap:
            buffer = [buffer[-1]]
            carried_only = True
        else:
            buffer = []
            carried_only = False

    for block in blocks:
        if block.headings != (section or []):
            emit(carry_overlap=False)
            section = block.headings
        candidate = estimate_tokens(" ".join([*buffer, block.text]))
        if buffer and candidate > TARGET_TOKENS:
            emit(carry_overlap=True)
        # A single oversized paragraph is split hard at the max budget.
        text = block.text
        while estimate_tokens(text) > MAX_TOKENS:
            cut = MAX_TOKENS * 4
            buffer.append(text[:cut])
            carried_only = False
            emit(carry_overlap=False)
            text = text[cut:]
        buffer.append(text)
        carried_only = False
    emit(carry_overlap=False)
    return chunks
