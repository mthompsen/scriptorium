package com.scriptorium.retrieval.legacyadmin;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.httpBasic;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.forwardedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.DocumentSummary;
import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.GraphStats;
import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.TenantCorpus;
import com.scriptorium.retrieval.ollama.EmbeddingClient;
import com.scriptorium.retrieval.opensearch.SearchGateway;
import com.scriptorium.retrieval.retrieve.RetrievedChunk;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

/**
 * The security split of ADR-0009: the legacy console demands HTTP Basic,
 * while the internal REST API keeps working unauthenticated (and without
 * CSRF tokens) exactly as before M7.
 */
@SpringBootTest
@AutoConfigureMockMvc
class LegacyAdminSecurityTest {

    @Autowired private MockMvc mockMvc;

    @Test
    void consoleRejectsAnonymousRequests() throws Exception {
        mockMvc.perform(get("/legacy/admin/")).andExpect(status().isUnauthorized());
        mockMvc.perform(get("/legacy/admin/api/tenants")).andExpect(status().isUnauthorized());
    }

    @Test
    void consoleAcceptsBasicAuthAndForwardsToJsp() throws Exception {
        mockMvc.perform(get("/legacy/admin/").with(httpBasic("admin", "scriptorium-dev")))
                .andExpect(status().isOk())
                .andExpect(forwardedUrl("/WEB-INF/jsp/legacy/index.jsp"));
        mockMvc.perform(
                        get("/legacy/admin/api/tenants")
                                .with(httpBasic("admin", "scriptorium-dev")))
                .andExpect(status().isOk());
    }

    @Test
    void consoleRejectsWrongCredentials() throws Exception {
        mockMvc.perform(get("/legacy/admin/").with(httpBasic("admin", "wrong")))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void internalApiStaysOpenAndCsrfFree() throws Exception {
        mockMvc.perform(get("/health")).andExpect(status().isOk());
        // POST without a CSRF token must not be rejected (service-to-service).
        mockMvc.perform(
                        post("/retrieve")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"tenant_id": "0f9a1c2e-3b4d-5e6f-8a9b-0c1d2e3f4a5b",
                                         "query": "pto policy"}
                                        """))
                .andExpect(status().isOk());
    }

    @TestConfiguration
    static class StubBackends {

        @Bean
        @Primary
        SearchGateway searchGateway() {
            return new SearchGateway() {
                @Override
                public List<RetrievedChunk> bm25(String tenantId, String query, int size) {
                    return List.of();
                }

                @Override
                public List<RetrievedChunk> knn(
                        String tenantId, List<Double> embedding, int size) {
                    return List.of();
                }

                @Override
                public List<RetrievedChunk> fetchChunks(
                        String tenantId, String documentId, int fromOrdinal, int toOrdinal) {
                    return List.of();
                }
            };
        }

        @Bean
        @Primary
        EmbeddingClient embeddingClient() {
            return text -> List.of(0.1, 0.2, 0.3);
        }

        @Bean
        @Primary
        CorpusAdminPort corpusAdminPort() {
            return new CorpusAdminPort() {
                @Override
                public List<TenantCorpus> tenantCorpora() {
                    return List.of(new TenantCorpus("t-1", 1));
                }

                @Override
                public List<DocumentSummary> documents(String tenantId) {
                    return List.of();
                }
            };
        }

        @Bean
        @Primary
        GraphAdminPort graphAdminPort() {
            return tenantId -> new GraphStats(0, 0);
        }
    }
}
