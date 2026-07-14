package com.scriptorium.retrieval.contract;

import au.com.dius.pact.provider.junit5.HttpTestTarget;
import au.com.dius.pact.provider.junit5.PactVerificationContext;
import au.com.dius.pact.provider.junit5.PactVerificationInvocationContextProvider;
import au.com.dius.pact.provider.junitsupport.Provider;
import au.com.dius.pact.provider.junitsupport.State;
import au.com.dius.pact.provider.junitsupport.loader.PactFolder;
import com.scriptorium.retrieval.graph.GraphModels.EntityHit;
import com.scriptorium.retrieval.graph.GraphModels.GraphContextEntry;
import com.scriptorium.retrieval.graph.GraphModels.GraphEdge;
import com.scriptorium.retrieval.graph.GraphModels.GraphNode;
import com.scriptorium.retrieval.graph.GraphModels.Neighborhood;
import com.scriptorium.retrieval.graph.GraphStore;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.TestTemplate;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;

/**
 * Verifies the committed consumer contract (packages/contracts/pacts,
 * ADR-0006) against the real HTTP layer with a stubbed graph adapter.
 */
@Provider("retrieval")
@PactFolder("../../packages/contracts/pacts")
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class PactVerificationTest {

    @LocalServerPort private int port;

    @BeforeEach
    void setTarget(PactVerificationContext context) {
        context.setTarget(new HttpTestTarget("localhost", port));
    }

    @TestTemplate
    @ExtendWith(PactVerificationInvocationContextProvider.class)
    void verifyContract(PactVerificationContext context) {
        context.verifyInteraction();
    }

    @State("entities exist for the demo tenant")
    void entitiesExist() {
        // Stub data lives in the fake below; nothing to arrange.
    }

    @State("entity abc123def456 has related entities")
    void neighborhoodExists() {
        // Stub data lives in the fake below; nothing to arrange.
    }

    @TestConfiguration
    static class StubGraph {

        @Bean
        @Primary
        GraphStore graphStore() {
            return new GraphStore() {
                @Override
                public List<EntityHit> searchEntities(String tenantId, String query, int limit) {
                    return List.of(
                            new EntityHit("abc123def456", "Aurelia Corp", "organization", 4));
                }

                @Override
                public Neighborhood neighborhood(String tenantId, String entityId) {
                    return new Neighborhood(
                            List.of(
                                    new GraphNode("abc123def456", "Aurelia Corp", "organization"),
                                    new GraphNode("def456abc123", "PTO Policy", "policy")),
                            List.of(new GraphEdge(
                                    "abc123def456", "def456abc123", "owns", 0.9)));
                }

                @Override
                public List<GraphContextEntry> contextForChunks(
                        String tenantId, List<String> chunkIds) {
                    return List.of();
                }
            };
        }
    }
}
