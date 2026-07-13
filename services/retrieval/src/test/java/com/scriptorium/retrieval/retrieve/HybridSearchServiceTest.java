package com.scriptorium.retrieval.retrieve;

import static org.assertj.core.api.Assertions.assertThat;

import com.scriptorium.retrieval.ollama.EmbeddingClient;
import com.scriptorium.retrieval.opensearch.SearchGateway;
import java.util.List;
import org.junit.jupiter.api.Test;

class HybridSearchServiceTest {

    private static RetrievedChunk chunk(String id) {
        return new RetrievedChunk(id, "doc", "text", 1.0);
    }

    private final EmbeddingClient fakeEmbedder = text -> List.of(0.1, 0.2, 0.3);

    @Test
    void fusesLexicalAndVectorResultsWithOverfetch() {
        SearchGateway gateway = new SearchGateway() {
            @Override
            public List<RetrievedChunk> bm25(String tenantId, String query, int size) {
                assertThat(size).isEqualTo(6); // k * overfetch
                return List.of(chunk("lex1"), chunk("shared"));
            }

            @Override
            public List<RetrievedChunk> knn(String tenantId, List<Double> embedding, int size) {
                assertThat(embedding).containsExactly(0.1, 0.2, 0.3);
                return List.of(chunk("shared"), chunk("vec1"));
            }
        };

        List<RetrievedChunk> results =
                new HybridSearchService(gateway, fakeEmbedder).retrieve("tenant-1", "query", 3);

        assertThat(results.get(0).chunkId()).isEqualTo("shared");
        assertThat(results).hasSize(3);
    }

    @Test
    void emptyIndexYieldsEmptyResultsNotAnError() {
        SearchGateway emptyGateway = new SearchGateway() {
            @Override
            public List<RetrievedChunk> bm25(String tenantId, String query, int size) {
                return List.of();
            }

            @Override
            public List<RetrievedChunk> knn(String tenantId, List<Double> embedding, int size) {
                return List.of();
            }
        };

        assertThat(new HybridSearchService(emptyGateway, fakeEmbedder)
                .retrieve("tenant-1", "query", 8)).isEmpty();
    }
}
