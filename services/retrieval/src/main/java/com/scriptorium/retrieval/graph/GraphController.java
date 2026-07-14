package com.scriptorium.retrieval.graph;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import com.scriptorium.retrieval.graph.GraphModels.EntityHit;
import com.scriptorium.retrieval.graph.GraphModels.Neighborhood;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.util.List;
import java.util.UUID;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** Graph query endpoints (ARCHITECTURE.md Section 7.3). */
@RestController
@Validated
public class GraphController {

    private final GraphStore graphStore;

    public GraphController(GraphStore graphStore) {
        this.graphStore = graphStore;
    }

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record SearchResponse(List<EntityHit> entities) {}

    @GetMapping("/graph/search")
    public SearchResponse search(
            @RequestParam("tenant_id") UUID tenantId,
            @RequestParam("q") @NotBlank @Size(max = 200) String query) {
        return new SearchResponse(graphStore.searchEntities(tenantId.toString(), query, 20));
    }

    @GetMapping("/graph/entity/{entityId}/neighborhood")
    public Neighborhood neighborhood(
            @PathVariable String entityId, @RequestParam("tenant_id") UUID tenantId) {
        return graphStore.neighborhood(tenantId.toString(), entityId);
    }
}
