package com.scriptorium.retrieval.legacyadmin;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

/** Wire and view types for the legacy admin console (Section 7.3, RP5). */
public final class LegacyAdminModels {

    private LegacyAdminModels() {}

    /** One tenant's chunk index as seen in OpenSearch. */
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record TenantCorpus(String tenantId, long chunkCount) {}

    /** One indexed document inside a tenant corpus. */
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record DocumentSummary(String documentId, long chunkCount, String preview) {}

    /** Knowledge-graph footprint of one tenant. */
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record GraphStats(long entityCount, long relationCount) {}

    /** Row on the console dashboard: corpus joined with graph stats. */
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record TenantSummary(
            String tenantId, long chunkCount, long entityCount, long relationCount) {}
}
