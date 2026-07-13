from scriptorium_llm.base import StreamEvent

from agent_service.loop import BUDGET_REFUSAL, REFUSAL, AgentLoop
from agent_service.pii import BasicPiiFilter
from agent_service.tools import build_registry

CHUNK = {"chunk_id": "ab12cd34-0", "document_id": "doc-1", "text": "PTO is 25 days.", "score": 1.0}


class FakeRetrieval:
    def retrieve(self, tenant_id, query, k):
        return [CHUNK]

    def fetch_chunks(self, tenant_id, document_id, from_ordinal, to_ordinal):
        return [CHUNK]


class FakeCatalog:
    def list_recent(self, tenant_id, limit):
        return []


class FakeTrace:
    def __init__(self) -> None:
        self.steps: list[tuple] = []
        self.finished: tuple | None = None

    def create_run(self, tenant_id) -> str:
        return "run-1"

    def add_step(self, run_id, step_index, kind, tool_name, input_json, output_json, tokens=0):
        self.steps.append((step_index, kind, tool_name))

    def finish_run(self, run_id, status, total_tokens, latency_ms):
        self.finished = (status, total_tokens)


class ScriptedLLM:
    """Each chat_stream call yields the next scripted turn."""

    def __init__(self, turns: list[list[StreamEvent]]) -> None:
        self._turns = list(turns)

    def chat_stream(self, messages, tools=None):
        yield from self._turns.pop(0)


def search_turn() -> list[StreamEvent]:
    return [
        StreamEvent(type="tool_call", tool_name="search_documents", tool_input={"query": "pto"}),
        StreamEvent(type="done", usage={"input": 100, "output": 10}),
    ]


def final_turn(text: str) -> list[StreamEvent]:
    return [
        StreamEvent(type="content_delta", text=text),
        StreamEvent(type="done", usage={"input": 50, "output": 20}),
    ]


def build_loop(llm, trace=None, **kwargs) -> AgentLoop:
    return AgentLoop(
        llm,
        build_registry(FakeRetrieval(), FakeCatalog()),
        trace or FakeTrace(),
        **kwargs,
    )


def run_events(loop: AgentLoop, question: str = "PTO?") -> list:
    return list(loop.run("tenant-1", question))


def test_tool_call_then_grounded_final_answer() -> None:
    trace = FakeTrace()
    llm = ScriptedLLM([search_turn(), final_turn("PTO is 25 days [ab12cd34-0].")])

    events = run_events(build_loop(llm, trace))

    types = [e.type for e in events]
    assert types == ["run_start", "tool", "token", "final"]
    assert events[1].data["name"] == "search_documents"
    final = events[-1].data
    assert final["grounded"] is True
    assert final["citations"][0]["chunk_id"] == "ab12cd34-0"
    assert final["total_tokens"] == 180
    assert [(kind, tool) for _, kind, tool in trace.steps] == [
        ("tool", "search_documents"),
        ("final", None),
    ]
    assert trace.finished == ("succeeded", 180)


def test_unresolved_citations_are_stripped() -> None:
    llm = ScriptedLLM([search_turn(), final_turn("Fact [ab12cd34-0]. Fake [deadbeef-7].")])

    final = run_events(build_loop(llm))[-1].data

    assert "[deadbeef-7]" not in final["answer"]
    assert final["stripped_citations"] == 1


def test_answer_without_any_retrieval_is_refused() -> None:
    trace = FakeTrace()
    llm = ScriptedLLM([final_turn("Paris is the capital of France.")])

    final = run_events(build_loop(llm, trace), "capital of France?")[-1].data

    assert final["answer"] == REFUSAL
    assert final["grounded"] is False
    assert trace.finished[0] == "refused"


def test_step_budget_forces_refusal() -> None:
    trace = FakeTrace()
    llm = ScriptedLLM([search_turn() for _ in range(10)])

    final = run_events(build_loop(llm, trace, max_steps=3))[-1].data

    assert final["answer"] == BUDGET_REFUSAL
    assert trace.finished[0] == "refused"


def test_wall_clock_budget_forces_refusal() -> None:
    ticks = iter([0.0, 0.0, 500.0, 500.0, 500.0, 500.0])
    llm = ScriptedLLM([search_turn(), final_turn("too late")])

    final = run_events(
        build_loop(llm, timeout_s=240.0, clock=lambda: next(ticks))
    )[-1].data

    assert final["answer"] == BUDGET_REFUSAL


def test_invalid_tool_input_is_surfaced_and_loop_recovers() -> None:
    bad_turn = [
        StreamEvent(type="tool_call", tool_name="search_documents", tool_input={"k": 999}),
        StreamEvent(type="done", usage={}),
    ]
    llm = ScriptedLLM([bad_turn, search_turn(), final_turn("PTO is 25 days [ab12cd34-0].")])

    events = run_events(build_loop(llm))

    tool_events = [e for e in events if e.type == "tool"]
    assert "error" in tool_events[0].data["summary"]
    assert events[-1].data["grounded"] is True


def test_pii_filter_redacts_final_answer() -> None:
    llm = ScriptedLLM(
        [search_turn(), final_turn("The SSN on file is 123-45-6789 [ab12cd34-0].")]
    )

    final = run_events(build_loop(llm, pii_filter=BasicPiiFilter()))[-1].data

    assert "123-45-6789" not in final["answer"]
    assert "[REDACTED-SSN]" in final["answer"]
    assert final["pii_redactions"] == 1


def test_llm_failure_marks_run_failed_with_error_event() -> None:
    class ExplodingLLM:
        def chat_stream(self, messages, tools=None):
            raise ConnectionError("ollama down")
            yield  # pragma: no cover

    trace = FakeTrace()

    final = run_events(build_loop(ExplodingLLM(), trace))[-1].data

    assert final["grounded"] is False
    assert "error" in final
    assert trace.finished[0] == "failed"
