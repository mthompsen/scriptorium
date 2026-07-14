package com.scriptorium.retrieval.retrieve;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import com.scriptorium.retrieval.graph.GraphModels.GraphContextEntry;
import com.scriptorium.retrieval.graph.GraphStore;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RetrieveController {

    private static final Logger log = LoggerFactory.getLogger(RetrieveController.class);

    private final HybridSearchService hybridSearch;
    private final GraphStore graphStore;

    public RetrieveController(HybridSearchService hybridSearch, GraphStore graphStore) {
        this.hybridSearch = hybridSearch;
        this.graphStore = graphStore;
    }

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record RetrieveRequest(
            @NotNull UUID tenantId,
            @NotBlank @Size(max = 2000) String query,
            @Min(1) @Max(20) Integer k) {

        int effectiveK() {
            return k == null ? 8 : k;
        }
    }

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record RetrieveResponse(
            List<RetrievedChunk> results, String mode, List<GraphContextEntry> graphContext) {}

    @PostMapping("/retrieve")
    public RetrieveResponse retrieve(@Valid @RequestBody RetrieveRequest request) {
        String tenantId = request.tenantId().toString();
        List<RetrievedChunk> results =
                hybridSearch.retrieve(tenantId, request.query(), request.effectiveK());
        // Graph augmentation (ADR-0006): entity-linked context for the
        // returned chunks. If the graph is down, degrade to vector-only and
        // say so via the mode (Section 11 graceful degradation).
        List<GraphContextEntry> graphContext = List.of();
        String mode = "hybrid+graph";
        if (!results.isEmpty()) {
            try {
                graphContext = graphStore.contextForChunks(
                        tenantId, results.stream().map(RetrievedChunk::chunkId).toList());
            } catch (Exception e) {
                log.warn("graph unavailable; degrading to hybrid-only: {}", e.getMessage());
                mode = "hybrid";
            }
        }
        return new RetrieveResponse(results, mode, graphContext);
    }
}
