package com.scriptorium.retrieval.graph;

import com.scriptorium.retrieval.graph.GraphModels.EntityHit;
import com.scriptorium.retrieval.graph.GraphModels.GraphContextEntry;
import com.scriptorium.retrieval.graph.GraphModels.Neighborhood;
import java.util.List;

/** Port for the knowledge graph (ports-and-adapters, Section 7). */
public interface GraphStore {

    List<EntityHit> searchEntities(String tenantId, String query, int limit);

    Neighborhood neighborhood(String tenantId, String entityId);

    /** Entities mentioned by the given chunks with their strongest relations. */
    List<GraphContextEntry> contextForChunks(String tenantId, List<String> chunkIds);
}
