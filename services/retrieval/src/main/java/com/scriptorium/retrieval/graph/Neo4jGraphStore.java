package com.scriptorium.retrieval.graph;

import com.scriptorium.retrieval.graph.GraphModels.EntityHit;
import com.scriptorium.retrieval.graph.GraphModels.GraphContextEntry;
import com.scriptorium.retrieval.graph.GraphModels.GraphEdge;
import com.scriptorium.retrieval.graph.GraphModels.GraphNode;
import com.scriptorium.retrieval.graph.GraphModels.Neighborhood;
import com.scriptorium.retrieval.graph.GraphModels.RelatedEntity;
import com.scriptorium.retrieval.legacyadmin.GraphAdminPort;
import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.GraphStats;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.neo4j.driver.AuthTokens;
import org.neo4j.driver.Driver;
import org.neo4j.driver.GraphDatabase;
import org.neo4j.driver.Record;
import org.neo4j.driver.Session;
import org.neo4j.driver.Value;
import org.springframework.stereotype.Component;

/**
 * Neo4j adapter. Every query is parameterized Cypher with an explicit
 * tenant_id parameter — no string-built queries (Sections 8.5 and 12).
 */
@Component
public class Neo4jGraphStore implements GraphStore, GraphAdminPort {

    private final Driver driver;

    public Neo4jGraphStore(
            @org.springframework.beans.factory.annotation.Value("${scriptorium.neo4j.uri}")
                    String uri,
            @org.springframework.beans.factory.annotation.Value("${scriptorium.neo4j.user}")
                    String user,
            @org.springframework.beans.factory.annotation.Value("${scriptorium.neo4j.password}")
                    String password) {
        this.driver = GraphDatabase.driver(uri, AuthTokens.basic(user, password));
    }

    @Override
    public List<EntityHit> searchEntities(String tenantId, String query, int limit) {
        try (Session session = driver.session()) {
            return session.run(
                            """
                            MATCH (e:Entity {tenant_id: $tenant_id})
                            WHERE toLower(e.name) CONTAINS toLower($query)
                            OPTIONAL MATCH (c:Chunk)-[:MENTIONS]->(e)
                            RETURN e.id AS id, e.name AS name, e.type AS type,
                                   count(c) AS mentions
                            ORDER BY mentions DESC, name
                            LIMIT $limit
                            """,
                            Map.of("tenant_id", tenantId, "query", query, "limit", limit))
                    .list(r -> new EntityHit(
                            r.get("id").asString(),
                            r.get("name").asString(),
                            r.get("type").asString(),
                            r.get("mentions").asLong()));
        }
    }

    @Override
    public Neighborhood neighborhood(String tenantId, String entityId) {
        try (Session session = driver.session()) {
            List<Record> records = session.run(
                            """
                            MATCH (e:Entity {id: $entity_id, tenant_id: $tenant_id})
                            OPTIONAL MATCH (e)-[r:RELATED_TO]-(o:Entity {tenant_id: $tenant_id})
                            RETURN e.id AS id, e.name AS name, e.type AS type,
                                   o.id AS oid, o.name AS oname, o.type AS otype,
                                   r.relation AS relation, r.confidence AS confidence,
                                   CASE WHEN startNode(r) = e THEN 'out' ELSE 'in' END AS direction
                            """,
                            Map.of("entity_id", entityId, "tenant_id", tenantId))
                    .list();
            Map<String, GraphNode> nodes = new LinkedHashMap<>();
            List<GraphEdge> edges = new ArrayList<>();
            for (Record record : records) {
                nodes.putIfAbsent(
                        record.get("id").asString(),
                        new GraphNode(
                                record.get("id").asString(),
                                record.get("name").asString(),
                                record.get("type").asString()));
                if (record.get("oid").isNull()) {
                    continue;
                }
                GraphNode other = new GraphNode(
                        record.get("oid").asString(),
                        record.get("oname").asString(),
                        record.get("otype").asString());
                nodes.putIfAbsent(other.id(), other);
                boolean outgoing = "out".equals(record.get("direction").asString());
                edges.add(new GraphEdge(
                        outgoing ? record.get("id").asString() : other.id(),
                        outgoing ? other.id() : record.get("id").asString(),
                        record.get("relation").asString(""),
                        record.get("confidence").asDouble(0.0)));
            }
            return new Neighborhood(new ArrayList<>(nodes.values()), edges);
        }
    }

    @Override
    public List<GraphContextEntry> contextForChunks(String tenantId, List<String> chunkIds) {
        try (Session session = driver.session()) {
            return session.run(
                            """
                            MATCH (c:Chunk {tenant_id: $tenant_id})-[:MENTIONS]->(e:Entity)
                            WHERE c.id IN $chunk_ids
                            OPTIONAL MATCH (e)-[r:RELATED_TO]-(o:Entity {tenant_id: $tenant_id})
                            WITH e, collect(DISTINCT {name: o.name, relation: r.relation,
                                                      confidence: r.confidence}) AS related
                            RETURN e.id AS id, e.name AS name, e.type AS type,
                                   related[0..5] AS related
                            ORDER BY size(related) DESC, name
                            LIMIT 10
                            """,
                            Map.of("tenant_id", tenantId, "chunk_ids", chunkIds))
                    .list(Neo4jGraphStore::toContextEntry);
        }
    }

    @Override
    public GraphStats graphStats(String tenantId) {
        try (Session session = driver.session()) {
            long entities = session.run(
                            "MATCH (e:Entity {tenant_id: $tenant_id}) RETURN count(e) AS n",
                            Map.of("tenant_id", tenantId))
                    .single()
                    .get("n")
                    .asLong();
            long relations = session.run(
                            """
                            MATCH (:Entity {tenant_id: $tenant_id})
                                  -[r:RELATED_TO]->(:Entity {tenant_id: $tenant_id})
                            RETURN count(r) AS n
                            """,
                            Map.of("tenant_id", tenantId))
                    .single()
                    .get("n")
                    .asLong();
            return new GraphStats(entities, relations);
        }
    }

    private static GraphContextEntry toContextEntry(Record record) {
        List<RelatedEntity> related = new ArrayList<>();
        for (Value item : record.get("related").values()) {
            if (item.get("name").isNull()) {
                continue;
            }
            related.add(new RelatedEntity(
                    item.get("name").asString(),
                    item.get("relation").asString(""),
                    item.get("confidence").asDouble(0.0)));
        }
        return new GraphContextEntry(
                new GraphNode(
                        record.get("id").asString(),
                        record.get("name").asString(),
                        record.get("type").asString()),
                related);
    }
}
