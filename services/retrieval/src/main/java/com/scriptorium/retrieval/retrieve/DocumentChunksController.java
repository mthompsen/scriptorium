package com.scriptorium.retrieval.retrieve;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import com.scriptorium.retrieval.opensearch.SearchGateway;
import java.util.List;
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** Serves ordered chunk content for the agent's get_document tool (M3). */
@RestController
public class DocumentChunksController {

    private static final int MAX_WINDOW = 50;

    private final SearchGateway searchGateway;

    public DocumentChunksController(SearchGateway searchGateway) {
        this.searchGateway = searchGateway;
    }

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record ChunksResponse(List<RetrievedChunk> chunks) {}

    @GetMapping("/document/{documentId}/chunks")
    public ChunksResponse chunks(
            @PathVariable UUID documentId,
            @RequestParam("tenant_id") UUID tenantId,
            @RequestParam(name = "from", defaultValue = "0") int from,
            @RequestParam(name = "to", defaultValue = "19") int to) {
        int safeFrom = Math.max(0, from);
        int safeTo = Math.min(Math.max(safeFrom, to), safeFrom + MAX_WINDOW - 1);
        return new ChunksResponse(searchGateway.fetchChunks(
                tenantId.toString(), documentId.toString(), safeFrom, safeTo));
    }
}
