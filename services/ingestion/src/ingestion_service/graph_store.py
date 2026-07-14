"""Neo4j adapter for the knowledge graph (ARCHITECTURE.md Section 8.5, ADR-0006).

All Cypher is parameterized and tenant-filtered; no string-built queries.
Writes are idempotent per document: re-ingest replaces the document's chunks
and mentions, then prunes entities left without any mention.
"""

import hashlib

from neo4j import GraphDatabase

from ingestion_service.extraction import Relation


def entity_id(tenant_id: str, name: str, entity_type: str) -> str:
    """Deterministic tenant-scoped identity: same (name, type) merges.

    This is a content-address for graph node identity, not a security hash;
    SHA-256 (truncated) is used over SHA-1 to avoid the deprecated primitive.
    Only ingestion computes ids; retrieval reads them, so a hash change just
    re-keys entities on the next ingest.
    """
    raw = f"{tenant_id}|{name.lower()}|{entity_type}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


class Neo4jGraphStore:
    def __init__(self, uri: str, user: str, password: str) -> None:
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def replace_document_graph(
        self,
        tenant_id: str,
        document_id: str,
        title: str,
        chunks: list[dict],  # {chunk_id, ordinal, entities: list[Entity]}
        relations: list[Relation],
        entity_types: dict[str, str],  # entity name (lower) -> type
    ) -> None:
        with self._driver.session() as session:
            session.execute_write(
                self._write, tenant_id, document_id, title, chunks, relations, entity_types
            )

    @staticmethod
    def _write(tx, tenant_id, document_id, title, chunks, relations, entity_types) -> None:
        # 1. Drop the document's previous chunks (and their MENTIONS edges).
        tx.run(
            "MATCH (d:Document {id: $document_id, tenant_id: $tenant_id})"
            "-[:HAS_CHUNK]->(c:Chunk) DETACH DELETE c",
            document_id=document_id,
            tenant_id=tenant_id,
        )
        tx.run(
            "MERGE (d:Document {id: $document_id, tenant_id: $tenant_id}) "
            "SET d.title = $title",
            document_id=document_id,
            tenant_id=tenant_id,
            title=title,
        )
        # 2. Chunks + mentions, batched with UNWIND.
        chunk_rows = [
            {
                "chunk_id": chunk["chunk_id"],
                "ordinal": chunk["ordinal"],
                "entities": [
                    {
                        "id": entity_id(tenant_id, e.name, e.type),
                        "name": e.name,
                        "type": e.type,
                    }
                    for e in chunk["entities"]
                ],
            }
            for chunk in chunks
        ]
        tx.run(
            "MATCH (d:Document {id: $document_id, tenant_id: $tenant_id}) "
            "UNWIND $rows AS row "
            "MERGE (c:Chunk {id: row.chunk_id, tenant_id: $tenant_id}) "
            "SET c.ordinal = row.ordinal "
            "MERGE (d)-[:HAS_CHUNK]->(c) "
            "WITH c, row UNWIND row.entities AS ent "
            "MERGE (e:Entity {id: ent.id, tenant_id: $tenant_id}) "
            "SET e.name = ent.name, e.type = ent.type "
            "MERGE (c)-[:MENTIONS]->(e)",
            document_id=document_id,
            tenant_id=tenant_id,
            rows=chunk_rows,
        )
        # 3. Entity-entity relations with confidence (Section 8.5).
        relation_rows = [
            {
                "source_id": entity_id(
                    tenant_id, r.source, entity_types.get(r.source.lower(), "other")
                ),
                "target_id": entity_id(
                    tenant_id, r.target, entity_types.get(r.target.lower(), "other")
                ),
                "relation": r.relation,
                "confidence": r.confidence,
            }
            for r in relations
        ]
        tx.run(
            "UNWIND $rows AS row "
            "MATCH (a:Entity {id: row.source_id, tenant_id: $tenant_id}) "
            "MATCH (b:Entity {id: row.target_id, tenant_id: $tenant_id}) "
            "MERGE (a)-[rel:RELATED_TO]->(b) "
            "SET rel.relation = row.relation, rel.confidence = row.confidence",
            tenant_id=tenant_id,
            rows=relation_rows,
        )
        # 4. Prune entities no chunk mentions anymore (tenant-scoped).
        tx.run(
            "MATCH (e:Entity {tenant_id: $tenant_id}) "
            "WHERE NOT (e)<-[:MENTIONS]-(:Chunk) DETACH DELETE e",
            tenant_id=tenant_id,
        )
