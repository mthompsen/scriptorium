package com.scriptorium.retrieval.graph;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import java.util.List;

/** Wire types for graph queries (Section 8.5 model, snake_case contract). */
public final class GraphModels {

    private GraphModels() {}

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record EntityHit(String id, String name, String type, long mentionCount) {}

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record GraphNode(String id, String name, String type) {}

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record GraphEdge(String source, String target, String relation, double confidence) {}

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record Neighborhood(List<GraphNode> nodes, List<GraphEdge> edges) {}

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record RelatedEntity(String name, String relation, double confidence) {}

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record GraphContextEntry(GraphNode entity, List<RelatedEntity> related) {}
}
