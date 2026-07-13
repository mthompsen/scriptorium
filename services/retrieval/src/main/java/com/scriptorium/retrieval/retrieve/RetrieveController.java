package com.scriptorium.retrieval.retrieve;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;
import java.util.UUID;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RetrieveController {

    private final HybridSearchService hybridSearch;

    public RetrieveController(HybridSearchService hybridSearch) {
        this.hybridSearch = hybridSearch;
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
    public record RetrieveResponse(List<RetrievedChunk> results, String mode) {}

    @PostMapping("/retrieve")
    public RetrieveResponse retrieve(@Valid @RequestBody RetrieveRequest request) {
        List<RetrievedChunk> results = hybridSearch.retrieve(
                request.tenantId().toString(), request.query(), request.effectiveK());
        return new RetrieveResponse(results, "hybrid");
    }
}
