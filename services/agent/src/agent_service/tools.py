"""The agent's tool set (DESIGN.md Section 9.2).

Every tool is a typed, allowlisted function: inputs are validated against a
JSON Schema before execution, and the tenant scope is injected server-side —
the model can never widen it. The model never executes arbitrary code.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import jsonschema


@dataclass
class ToolResult:
    output: Any  # JSON-safe payload returned to the model
    chunks: list[dict] = field(default_factory=list)  # citable chunks surfaced


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    execute: Callable[[str, dict], ToolResult]  # (tenant_id, validated_args)


class ToolValidationError(ValueError):
    pass


class ToolRegistry:
    def __init__(self, tools: list[Tool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def definitions(self) -> list[dict]:
        """Provider tool definitions (Ollama/OpenAI function format; the
        Bedrock adapter converts to toolSpec)."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in self._tools.values()
        ]

    def execute(self, tenant_id: str, name: str, args: dict) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolValidationError(f"tool '{name}' is not in the allowlist")
        try:
            jsonschema.validate(args, tool.input_schema)
        except jsonschema.ValidationError as error:
            raise ToolValidationError(f"invalid input for {name}: {error.message}") from error
        return tool.execute(tenant_id, args)


def build_registry(retrieval, catalog) -> ToolRegistry:
    def search_documents(tenant_id: str, args: dict) -> ToolResult:
        results = retrieval.retrieve(tenant_id, args["query"], args.get("k", 8))
        return ToolResult(
            output=[
                {"chunk_id": c["chunk_id"], "document_id": c["document_id"], "text": c["text"]}
                for c in results
            ],
            chunks=results,
        )

    def get_document(tenant_id: str, args: dict) -> ToolResult:
        chunks = retrieval.fetch_chunks(
            tenant_id, args["document_id"], args.get("from", 0), args.get("to", 19)
        )
        return ToolResult(
            output=[{"chunk_id": c["chunk_id"], "text": c["text"]} for c in chunks],
            chunks=chunks,
        )

    def list_recent(tenant_id: str, args: dict) -> ToolResult:
        return ToolResult(output=catalog.list_recent(tenant_id, args.get("limit", 10)))

    def query_knowledge_graph(tenant_id: str, args: dict) -> ToolResult:
        # Stub until M4 (ADR-0005): schema-stable, swaps to Neo4j later.
        return ToolResult(
            output={
                "results": [],
                "note": "the knowledge graph is not available yet (arrives in M4)",
            }
        )

    return ToolRegistry(
        [
            Tool(
                name="search_documents",
                description=(
                    "Retrieve the most relevant document chunks for a query "
                    "within the current tenant."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "minLength": 1, "maxLength": 2000},
                        "k": {"type": "integer", "minimum": 1, "maximum": 20, "default": 8},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                execute=search_documents,
            ),
            Tool(
                name="get_document",
                description="Fetch a window of chunks from one document by its id.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "pattern": "^[0-9a-fA-F-]{36}$",
                        },
                        "from": {"type": "integer", "minimum": 0, "default": 0},
                        "to": {"type": "integer", "minimum": 0, "default": 19},
                    },
                    "required": ["document_id"],
                    "additionalProperties": False,
                },
                execute=get_document,
            ),
            Tool(
                name="list_recent",
                description="List the most recently uploaded documents in the tenant.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10}
                    },
                    "additionalProperties": False,
                },
                execute=list_recent,
            ),
            Tool(
                name="query_knowledge_graph",
                description=(
                    "Query the knowledge graph for an entity and its relations. "
                    "Not yet populated; becomes useful in M4."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "entity": {"type": "string", "minLength": 1, "maxLength": 500}
                    },
                    "required": ["entity"],
                    "additionalProperties": False,
                },
                execute=query_knowledge_graph,
            ),
        ]
    )
