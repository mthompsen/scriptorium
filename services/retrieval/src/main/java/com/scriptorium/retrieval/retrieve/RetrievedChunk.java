package com.scriptorium.retrieval.retrieve;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

/** One ranked chunk with provenance (ARCHITECTURE.md Section 7.3). */
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record RetrievedChunk(String chunkId, String documentId, String text, double score) {

    public RetrievedChunk withScore(double newScore) {
        return new RetrievedChunk(chunkId, documentId, text, newScore);
    }
}
