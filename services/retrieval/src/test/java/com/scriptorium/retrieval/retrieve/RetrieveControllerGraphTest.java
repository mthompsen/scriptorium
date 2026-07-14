package com.scriptorium.retrieval.retrieve;

import static org.assertj.core.api.Assertions.assertThat;

import com.scriptorium.retrieval.graph.GraphModels.EntityHit;
import com.scriptorium.retrieval.graph.GraphModels.GraphContextEntry;
import com.scriptorium.retrieval.graph.GraphModels.GraphNode;
import com.scriptorium.retrieval.graph.GraphModels.Neighborhood;
import com.scriptorium.retrieval.graph.GraphModels.RelatedEntity;
import com.scriptorium.retrieval.graph.GraphStore;
import com.scriptorium.retrieval.ollama.EmbeddingClient;
import com.scriptorium.retrieval.opensearch.SearchGateway;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class RetrieveControllerGraphTest {

    private static final RetrievedChunk CHUNK =
            new RetrievedChunk("ab12cd34-0", "doc-1", "PTO is 25 days.", 0.03);

    private static final SearchGateway GATEWAY = new SearchGateway() {
        @Override
        public List<RetrievedChunk> bm25(String tenantId, String query, int size) {
            return List.of(CHUNK);
        }

        @Override
        public List<RetrievedChunk> knn(String tenantId, List<Double> embedding, int size) {
            return List.of(CHUNK);
        }

        @Override
        public List<RetrievedChunk> fetchChunks(
                String tenantId, String documentId, int fromOrdinal, int toOrdinal) {
            return List.of();
        }
    };

    private static final EmbeddingClient EMBEDDER = text -> List.of(0.1, 0.2);

    private RetrieveController.RetrieveRequest request() {
        return new RetrieveController.RetrieveRequest(UUID.randomUUID(), "PTO?", 4);
    }

    @Test
    void retrieveAttachesGraphContextForReturnedChunks() {
        GraphStore graph = new StubGraph(
                List.of(new GraphContextEntry(
                        new GraphNode("e1", "PTO Policy", "policy"),
                        List.of(new RelatedEntity("Aurelia Corp", "owned by", 0.9)))),
                false);

        var response = new RetrieveController(
                        new HybridSearchService(GATEWAY, EMBEDDER), graph)
                .retrieve(request());

        assertThat(response.mode()).isEqualTo("hybrid+graph");
        assertThat(response.graphContext()).hasSize(1);
        assertThat(response.graphContext().get(0).entity().name()).isEqualTo("PTO Policy");
    }

    @Test
    void graphOutageDegradesToHybridOnlyWithoutFailing() {
        GraphStore graph = new StubGraph(List.of(), true);

        var response = new RetrieveController(
                        new HybridSearchService(GATEWAY, EMBEDDER), graph)
                .retrieve(request());

        assertThat(response.results()).isNotEmpty(); // retrieval still works
        assertThat(response.mode()).isEqualTo("hybrid"); // and says it degraded
        assertThat(response.graphContext()).isEmpty();
    }

    private record StubGraph(List<GraphContextEntry> entries, boolean explode)
            implements GraphStore {

        @Override
        public List<EntityHit> searchEntities(String tenantId, String query, int limit) {
            return List.of();
        }

        @Override
        public Neighborhood neighborhood(String tenantId, String entityId) {
            return new Neighborhood(List.of(), List.of());
        }

        @Override
        public List<GraphContextEntry> contextForChunks(String tenantId, List<String> chunkIds) {
            if (explode) {
                throw new IllegalStateException("neo4j down");
            }
            return entries;
        }
    }
}
