package com.scriptorium.retrieval.retrieve;

import static org.assertj.core.api.Assertions.assertThat;

import com.scriptorium.retrieval.opensearch.SearchGateway;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class DocumentChunksControllerTest {

    private record Window(int from, int to) {}

    private static final class RecordingGateway implements SearchGateway {
        Window window;

        @Override
        public List<RetrievedChunk> bm25(String tenantId, String query, int size) {
            return List.of();
        }

        @Override
        public List<RetrievedChunk> knn(String tenantId, List<Double> embedding, int size) {
            return List.of();
        }

        @Override
        public List<RetrievedChunk> fetchChunks(
                String tenantId, String documentId, int fromOrdinal, int toOrdinal) {
            window = new Window(fromOrdinal, toOrdinal);
            return List.of(new RetrievedChunk("c-0", documentId, "text", 1.0));
        }
    }

    @Test
    void clampsTheWindowToFiftyChunksAndNonNegativeBounds() {
        RecordingGateway gateway = new RecordingGateway();
        DocumentChunksController controller = new DocumentChunksController(gateway);

        controller.chunks(UUID.randomUUID(), UUID.randomUUID(), -5, 500);

        assertThat(gateway.window.from()).isZero();
        assertThat(gateway.window.to()).isEqualTo(49); // 50-chunk cap
    }

    @Test
    void returnsChunksFromTheGateway() {
        RecordingGateway gateway = new RecordingGateway();
        DocumentChunksController controller = new DocumentChunksController(gateway);

        var response = controller.chunks(UUID.randomUUID(), UUID.randomUUID(), 0, 9);

        assertThat(response.chunks()).hasSize(1);
        assertThat(gateway.window).isEqualTo(new Window(0, 9));
    }
}
