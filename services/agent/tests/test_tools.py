import pytest

from agent_service.tools import ToolValidationError, build_registry

CHUNK = {"chunk_id": "ab12cd34-0", "document_id": "doc-1", "text": "PTO is 25 days.", "score": 1.0}


class FakeRetrieval:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def retrieve(self, tenant_id, query, k):
        self.calls.append(("retrieve", tenant_id, query, k))
        return [CHUNK]

    def fetch_chunks(self, tenant_id, document_id, from_ordinal, to_ordinal):
        self.calls.append(("fetch_chunks", tenant_id, document_id, from_ordinal, to_ordinal))
        return [CHUNK]


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


def test_graph_tool_is_a_schema_stable_stub(registry) -> None:
    result = registry.execute("tenant-1", "query_knowledge_graph", {"entity": "Aurelia"})

    assert result.output["results"] == []
    assert "M4" in result.output["note"]
    assert result.chunks == []


def test_definitions_expose_all_four_tools(registry) -> None:
    names = [d["function"]["name"] for d in registry.definitions()]

    assert names == ["search_documents", "get_document", "list_recent", "query_knowledge_graph"]
