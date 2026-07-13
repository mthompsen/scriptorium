from ingestion_service.chunker import MAX_TOKENS, chunk
from ingestion_service.parsers import Block


def test_chunks_never_cross_heading_boundaries() -> None:
    blocks = [
        Block(headings=["A"], text="alpha " * 30),
        Block(headings=["B"], text="beta " * 30),
    ]

    chunks = chunk(blocks)

    assert len(chunks) == 2
    assert "alpha" in chunks[0].text and "beta" not in chunks[0].text
    assert chunks[0].headings == ["A"]
    assert chunks[1].headings == ["B"]


def test_long_sections_split_with_overlap() -> None:
    import re

    paragraphs = [
        Block(headings=["Long"], text=f"paragraph {i} " + "word " * 100) for i in range(8)
    ]

    chunks = chunk(paragraphs)

    assert len(chunks) > 1
    # Overlap: each chunk starts with the previous chunk's last paragraph.
    for previous, current in zip(chunks, chunks[1:], strict=False):
        previous_ids = re.findall(r"paragraph (\d+)", previous.text)
        current_ids = re.findall(r"paragraph (\d+)", current.text)
        assert current_ids[0] == previous_ids[-1]


def test_oversized_single_paragraph_is_hard_split() -> None:
    blocks = [Block(headings=[], text="x" * (MAX_TOKENS * 4 * 3))]

    chunks = chunk(blocks)

    assert len(chunks) >= 3
    assert all(c.token_count <= MAX_TOKENS + 1 for c in chunks)


def test_ordinals_are_sequential_and_heading_prefix_present() -> None:
    blocks = [Block(headings=["H1", "H2"], text="content here")]

    chunks = chunk(blocks)

    assert [c.ordinal for c in chunks] == list(range(len(chunks)))
    assert chunks[0].text.startswith("H1 › H2\n")
