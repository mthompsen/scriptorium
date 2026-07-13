package com.scriptorium.retrieval.retrieve;

import com.scriptorium.retrieval.ollama.EmbeddingClient;
import com.scriptorium.retrieval.opensearch.SearchGateway;
import java.util.List;
import org.springframework.stereotype.Service;

/** Hybrid retrieval: BM25 + kNN fused with RRF (DESIGN.md Section 7.3). */
@Service
public class HybridSearchService {

    /** Overfetch factor per list so fusion has enough candidates. */
    private static final int OVERFETCH = 2;

    private final SearchGateway searchGateway;
    private final EmbeddingClient embeddingClient;

    public HybridSearchService(SearchGateway searchGateway, EmbeddingClient embeddingClient) {
        this.searchGateway = searchGateway;
        this.embeddingClient = embeddingClient;
    }

    public List<RetrievedChunk> retrieve(String tenantId, String query, int k) {
        List<Double> embedding = embeddingClient.embed(query);
        List<RetrievedChunk> lexical = searchGateway.bm25(tenantId, query, k * OVERFETCH);
        List<RetrievedChunk> vector = searchGateway.knn(tenantId, embedding, k * OVERFETCH);
        return RrfFusion.fuse(List.of(lexical, vector), k);
    }
}
