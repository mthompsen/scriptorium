package com.scriptorium.retrieval.retrieve;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Reciprocal Rank Fusion (Section 7.3): score(d) = sum over result lists of
 * 1 / (K + rank). Rank-based, so lexical and vector scores need no
 * normalisation against each other.
 */
public final class RrfFusion {

    static final int RRF_K = 60;

    private RrfFusion() {}

    public static List<RetrievedChunk> fuse(
            List<List<RetrievedChunk>> resultLists, int limit) {
        Map<String, RetrievedChunk> byId = new LinkedHashMap<>();
        Map<String, Double> scores = new LinkedHashMap<>();

        for (List<RetrievedChunk> results : resultLists) {
            for (int rank = 0; rank < results.size(); rank++) {
                RetrievedChunk chunk = results.get(rank);
                byId.putIfAbsent(chunk.chunkId(), chunk);
                scores.merge(chunk.chunkId(), 1.0 / (RRF_K + rank + 1), Double::sum);
            }
        }

        List<RetrievedChunk> fused = new ArrayList<>();
        scores.entrySet().stream()
                .sorted(Map.Entry.<String, Double>comparingByValue(Comparator.reverseOrder()))
                .limit(limit)
                .forEach(entry -> fused.add(byId.get(entry.getKey()).withScore(entry.getValue())));
        return fused;
    }
}
