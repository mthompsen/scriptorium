package com.scriptorium.retrieval.graph;

import static org.assertj.core.api.Assertions.assertThat;

import com.scriptorium.retrieval.graph.GraphModels.EntityHit;
import com.scriptorium.retrieval.graph.GraphModels.GraphContextEntry;
import com.scriptorium.retrieval.graph.GraphModels.GraphEdge;
import com.scriptorium.retrieval.graph.GraphModels.GraphNode;
import com.scriptorium.retrieval.graph.GraphModels.Neighborhood;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class GraphControllerTest {

    private static final class FakeGraphStore implements GraphStore {
        String lastTenant;
        String lastQuery;

        @Override
        public List<EntityHit> searchEntities(String tenantId, String query, int limit) {
            lastTenant = tenantId;
            lastQuery = query;
            return List.of(new EntityHit("abc123", "Aurelia Corp", "organization", 4));
        }

        @Override
        public Neighborhood neighborhood(String tenantId, String entityId) {
            lastTenant = tenantId;
            return new Neighborhood(
                    List.of(
                            new GraphNode("abc123", "Aurelia Corp", "organization"),
                            new GraphNode("def456", "PTO Policy", "policy")),
                    List.of(new GraphEdge("abc123", "def456", "owns", 0.9)));
        }

        @Override
        public List<GraphContextEntry> contextForChunks(String tenantId, List<String> chunkIds) {
            return List.of();
        }
    }

    @Test
    void searchPassesTenantScopeAndReturnsEntities() {
        FakeGraphStore store = new FakeGraphStore();
        UUID tenant = UUID.randomUUID();

        var response = new GraphController(store).search(tenant, "aurelia");

        assertThat(store.lastTenant).isEqualTo(tenant.toString());
        assertThat(store.lastQuery).isEqualTo("aurelia");
        assertThat(response.entities()).hasSize(1);
        assertThat(response.entities().get(0).name()).isEqualTo("Aurelia Corp");
    }

    @Test
    void neighborhoodReturnsNodesAndDirectedEdges() {
        FakeGraphStore store = new FakeGraphStore();

        Neighborhood neighborhood =
                new GraphController(store).neighborhood("abc123", UUID.randomUUID());

        assertThat(neighborhood.nodes()).hasSize(2);
        assertThat(neighborhood.edges()).hasSize(1);
        assertThat(neighborhood.edges().get(0).relation()).isEqualTo("owns");
    }
}
