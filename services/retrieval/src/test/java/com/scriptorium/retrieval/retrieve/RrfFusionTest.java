package com.scriptorium.retrieval.retrieve;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.within;

import java.util.List;
import org.junit.jupiter.api.Test;

class RrfFusionTest {

    private static RetrievedChunk chunk(String id) {
        return new RetrievedChunk(id, "doc-" + id, "text " + id, 1.0);
    }

    @Test
    void chunksInBothListsOutrankSingleListChunks() {
        List<RetrievedChunk> lexical = List.of(chunk("a"), chunk("b"), chunk("c"));
        List<RetrievedChunk> vector = List.of(chunk("c"), chunk("d"));

        List<RetrievedChunk> fused = RrfFusion.fuse(List.of(lexical, vector), 4);

        // c appears in both lists (rank 3 + rank 1) and must win overall.
        assertThat(fused.get(0).chunkId()).isEqualTo("c");
        assertThat(fused).extracting(RetrievedChunk::chunkId)
                .containsExactlyInAnyOrder("a", "b", "c", "d");
    }

    @Test
    void scoresFollowTheRrfFormula() {
        List<RetrievedChunk> single = List.of(chunk("a"));

        List<RetrievedChunk> fused = RrfFusion.fuse(List.of(single, List.of()), 1);

        assertThat(fused.get(0).score())
                .isCloseTo(1.0 / (RrfFusion.RRF_K + 1), within(1e-9));
    }

    @Test
    void deduplicatesAcrossListsAndRespectsLimit() {
        List<RetrievedChunk> lexical = List.of(chunk("a"), chunk("b"));
        List<RetrievedChunk> vector = List.of(chunk("a"), chunk("b"));

        List<RetrievedChunk> fused = RrfFusion.fuse(List.of(lexical, vector), 1);

        assertThat(fused).hasSize(1);
        assertThat(fused.get(0).chunkId()).isEqualTo("a");
    }

    @Test
    void emptyInputsProduceEmptyOutput() {
        assertThat(RrfFusion.fuse(List.of(List.of(), List.of()), 5)).isEmpty();
    }
}
