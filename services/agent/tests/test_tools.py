import pytest

from agent_service.tools import ToolValidationError, build_registry

CHUNK = {"chunk_id": "ab12cd34-0", "document_id": "doc-1", "text": "PTO is 25 days.", "score": 1.0}


class FakeRetrieval:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.entities: list[dict] = [
            {"id": "abc123", "name": "Aurelia Corp", "type": "organization", "mention_count": 4}
        ]

    def retrieve(self, tenant_id, query, k):
        self.calls.append(("retrieve", tenant_id, query, k))
        return [CHUNK]

    def fetch_chunks(self, tenant_id, document_id, from_ordinal, to_ordinal):
        self.calls.append(("fetch_chunks", tenant_id, document_id, from_ordinal, to_ordinal))
        return [CHUNK]

    def graph_search(self, tenant_id, query):
        self.calls.append(("graph_search", tenant_id, query))
        return self.entities

    def graph_neighborhood(self, tenant_id, entity_id):
        self.calls.append(("graph_neighborhood", tenant_id, entity_id))
        return {
            "nodes": [
                {"id": "abc123", "name": "Aurelia Corp", "type": "organization"},
                {"id": "def456", "name": "PTO Policy", "type": "policy"},
            ],
            "edges": [
                {"source": "abc123", "target": "def456", "relation": "owns", "confidence": 0.9}
            ],
        }


class FakeCatalog:
    def list_recent(self, tenant_id, limit):
        return [{"id": "doc-1", "title": "handbook.md", "status": "indexed", "created_at": "…"}]


@pytest.fixture
def registry():
    return build_registry(FakeRetrieval(), FakeCatalog())


def test_search_documents_surfaces_citable_chunks(registry) -> None:
    result = registry.execute("tenant-1", "search_documents", {"query": "pto", "k": 3})

    assert result.chunks == [CHUNK]
    assert result.output[0]["chunk_id"] == "ab12cd34-0"


def test_unknown_tool_is_rejected_by_the_allowlist(registry) -> None:
    with pytest.raises(ToolValidationError, match="allowlist"):
        registry.execute("tenant-1", "run_shell_command", {"cmd": "rm -rf /"})


def test_stringified_integers_from_small_models_are_coerced() -> None:
    """Regression: llama3.2:3b emits {"k": "10"}; validation must not reject it."""
    retrieval = FakeRetrieval()
    registry = build_registry(retrieval, FakeCatalog())

    result = registry.execute("tenant-1", "search_documents", {"query": "pto", "k": "10"})

    assert result.chunks == [CHUNK]
    called = next(c for c in retrieval.calls if c[0] == "retrieve")
    assert called[3] == 10  # executor received a real int
    assert isinstance(called[3], int)


def test_integral_floats_and_window_strings_are_coerced() -> None:
    retrieval = FakeRetrieval()
    registry = build_registry(retrieval, FakeCatalog())

    registry.execute("tenant-1", "search_documents", {"query": "pto", "k": 10.0})
    registry.execute(
        "tenant-1",
        "get_document",
        {"document_id": "11111111-1111-4111-8111-111111111111", "from": "0", "to": "5"},
    )

    retrieve_call = next(c for c in retrieval.calls if c[0] == "retrieve")
    assert retrieve_call[3] == 10 and isinstance(retrieve_call[3], int)
    fetch_call = next(c for c in retrieval.calls if c[0] == "fetch_chunks")
    assert fetch_call[3] == 0 and fetch_call[4] == 5


def test_coercion_stays_conservative_for_genuinely_bad_input(registry) -> None:
    with pytest.raises(ToolValidationError, match="invalid input"):
        registry.execute("tenant-1", "search_documents", {"query": "x", "k": "abc"})
    with pytest.raises(ToolValidationError, match="invalid input"):
        registry.execute("tenant-1", "search_documents", {"query": "x", "k": "10.5"})
    with pytest.raises(ToolValidationError, match="invalid input"):
        registry.execute("tenant-1", "search_documents", {"query": "x", "k": "999"})


def test_inputs_are_schema_validated_before_execution(registry) -> None:
    with pytest.raises(ToolValidationError, match="invalid input"):
        registry.execute("tenant-1", "search_documents", {"query": "x", "k": 999})
    with pytest.raises(ToolValidationError, match="invalid input"):
        registry.execute("tenant-1", "search_documents", {})
    with pytest.raises(ToolValidationError, match="invalid input"):
        registry.execute(
            "tenant-1", "search_documents", {"query": "x", "unexpected": "field"}
        )
    with pytest.raises(ToolValidationError, match="invalid input"):
        registry.execute(
            "tenant-1", "get_document", {"document_id": "'; DROP TABLE documents; --"}
        )


def test_tenant_scope_is_injected_server_side() -> None:
    retrieval = FakeRetrieval()
    registry = build_registry(retrieval, FakeCatalog())

    # Even if the model tried to smuggle a tenant into the args, the schema
    # rejects it (additionalProperties: false)...
    with pytest.raises(ToolValidationError):
        registry.execute("tenant-1", "search_documents", {"query": "x", "tenant_id": "other"})

    # ...and the executed call carries the server-side tenant.
    registry.execute("tenant-1", "search_documents", {"query": "x"})
    assert retrieval.calls[0][1] == "tenant-1"


def test_graph_tool_searches_then_expands_the_top_entity() -> None:
    retrieval = FakeRetrieval()
    registry = build_registry(retrieval, FakeCatalog())

    result = registry.execute("tenant-1", "query_knowledge_graph", {"entity": "Aurelia"})

    assert result.output["entity"]["name"] == "Aurelia Corp"
    assert len(result.output["edges"]) == 1
    assert result.output["edges"][0]["relation"] == "owns"
    assert ("graph_search", "tenant-1", "Aurelia") in retrieval.calls
    assert ("graph_neighborhood", "tenant-1", "abc123") in retrieval.calls


def test_graph_tool_reports_no_matches_cleanly() -> None:
    retrieval = FakeRetrieval()
    retrieval.entities = []
    registry = build_registry(retrieval, FakeCatalog())

    result = registry.execute("tenant-1", "query_knowledge_graph", {"entity": "Nobody"})

    assert result.output == {"results": [], "note": "no matching entities"}


def test_definitions_expose_all_four_tools(registry) -> None:
    names = [d["function"]["name"] for d in registry.definitions()]

    assert names == ["search_documents", "get_document", "list_recent", "query_knowledge_graph"]
