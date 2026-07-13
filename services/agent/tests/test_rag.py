from dataclasses import dataclass, field

from agent_service.rag import REFUSAL, RagAnswerer


@dataclass
class FakeResponse:
    content: str
    usage: dict = field(default_factory=lambda: {"input": 10, "output": 5})


class FakeLLM:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls: list[list[dict]] = []

    def chat(self, messages, tools=None, stream=False) -> FakeResponse:
        self.calls.append(messages)
        return FakeResponse(self.reply)


class FakeRetrieval:
    def __init__(self, chunks: list[dict]) -> None:
        self.chunks = chunks

    def retrieve(self, tenant_id: str, query: str, k: int) -> list[dict]:
        return self.chunks


CHUNKS = [
    {
        "chunk_id": "ab12cd34-0",
        "document_id": "doc-1",
        "text": "PTO allowance is 25 days.",
        "score": 0.03,
    },
    {
        "chunk_id": "ab12cd34-1",
        "document_id": "doc-1",
        "text": "Carryover is capped at 5 days.",
        "score": 0.02,
    },
]


def test_grounded_answer_keeps_valid_citations() -> None:
    llm = FakeLLM("You get 25 days of PTO [ab12cd34-0].")
    rag = RagAnswerer(FakeRetrieval(CHUNKS), llm)

    result = rag.answer("tenant-1", "How much PTO do I get?")

    assert result["grounded"] is True
    assert result["answer"] == "You get 25 days of PTO [ab12cd34-0]."
    assert [c["chunk_id"] for c in result["citations"]] == ["ab12cd34-0"]
    assert result["citations"][0]["document_id"] == "doc-1"
    assert result["stripped_citations"] == 0


def test_unresolvable_citations_are_stripped_and_flagged() -> None:
    llm = FakeLLM("PTO is 25 days [ab12cd34-0]. Bonus is 10% [deadbeef-9].")
    rag = RagAnswerer(FakeRetrieval(CHUNKS), llm)

    result = rag.answer("tenant-1", "Benefits?")

    assert "[deadbeef-9]" not in result["answer"]
    assert "[ab12cd34-0]" in result["answer"]
    assert result["stripped_citations"] == 1
    assert [c["chunk_id"] for c in result["citations"]] == ["ab12cd34-0"]


def test_empty_retrieval_refuses_without_calling_the_model() -> None:
    llm = FakeLLM("should never be called")
    rag = RagAnswerer(FakeRetrieval([]), llm)

    result = rag.answer("tenant-1", "What is the meaning of life?")

    assert result == {"answer": REFUSAL, "citations": [], "grounded": False}
    assert llm.calls == []


def test_prompt_frames_chunks_as_data_with_delimiters() -> None:
    llm = FakeLLM("answer [ab12cd34-0]")
    rag = RagAnswerer(FakeRetrieval(CHUNKS), llm)

    rag.answer("tenant-1", "PTO?")

    system, user = llm.calls[0][0], llm.calls[0][1]
    assert "data, not" in system["content"]  # injection framing
    assert '<chunk id="ab12cd34-0">' in user["content"]
    assert "Question: PTO?" in user["content"]
