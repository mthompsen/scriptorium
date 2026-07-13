package com.scriptorium.retrieval.opensearch;

import com.scriptorium.retrieval.retrieve.RetrievedChunk;
import java.util.List;

/** Port for the search backend (ports-and-adapters, Section 7). */
public interface SearchGateway {

    List<RetrievedChunk> bm25(String tenantId, String query, int size);

    List<RetrievedChunk> knn(String tenantId, List<Double> embedding, int size);
}
