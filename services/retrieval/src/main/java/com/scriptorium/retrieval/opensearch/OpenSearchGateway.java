package com.scriptorium.retrieval.opensearch;

import com.fasterxml.jackson.databind.JsonNode;
import com.scriptorium.retrieval.legacyadmin.CorpusAdminPort;
import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.DocumentSummary;
import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.TenantCorpus;
import com.scriptorium.retrieval.retrieve.RetrievedChunk;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestClient;

/** OpenSearch REST adapter. One index per tenant: chunks-&lt;tenant&gt; (ADR-0004). */
@Component
public class OpenSearchGateway implements SearchGateway, CorpusAdminPort {

    private final RestClient restClient;

    public OpenSearchGateway(@Value("${scriptorium.opensearch.url}") String baseUrl) {
        this.restClient = RestClient.builder().baseUrl(baseUrl).build();
    }

    @Override
    public List<RetrievedChunk> bm25(String tenantId, String query, int size) {
        Map<String, Object> body = Map.of(
                "size", size,
                "_source", List.of("chunk_id", "document_id", "text"),
                "query", Map.of("match", Map.of("text", Map.of("query", query))));
        return search(tenantId, body);
    }

    @Override
    public List<RetrievedChunk> knn(String tenantId, List<Double> embedding, int size) {
        Map<String, Object> body = Map.of(
                "size", size,
                "_source", List.of("chunk_id", "document_id", "text"),
                "query", Map.of("knn", Map.of("embedding",
                        Map.of("vector", embedding, "k", size))));
        return search(tenantId, body);
    }

    @Override
    public List<RetrievedChunk> fetchChunks(
            String tenantId, String documentId, int fromOrdinal, int toOrdinal) {
        Map<String, Object> body = Map.of(
                "size", toOrdinal - fromOrdinal + 1,
                "_source", List.of("chunk_id", "document_id", "text"),
                "sort", List.of(Map.of("ordinal", "asc")),
                "query", Map.of("bool", Map.of("filter", List.of(
                        Map.of("term", Map.of("document_id", documentId)),
                        Map.of("range", Map.of("ordinal",
                                Map.of("gte", fromOrdinal, "lte", toOrdinal)))))));
        return search(tenantId, body);
    }

    private static final String INDEX_PREFIX = "chunks-";
    private static final int PREVIEW_CHARS = 160;

    @Override
    public List<TenantCorpus> tenantCorpora() {
        JsonNode response;
        try {
            response = restClient.get()
                    .uri("/_cat/indices/{pattern}?format=json&h=index,docs.count", INDEX_PREFIX + "*")
                    .retrieve()
                    .body(JsonNode.class);
        } catch (HttpClientErrorException.NotFound e) {
            // No tenant has indexed anything yet.
            return List.of();
        }
        List<TenantCorpus> corpora = new ArrayList<>();
        for (JsonNode row : response) {
            String index = row.path("index").asText();
            corpora.add(new TenantCorpus(
                    index.substring(INDEX_PREFIX.length()),
                    row.path("docs.count").asLong()));
        }
        corpora.sort((a, b) -> a.tenantId().compareTo(b.tenantId()));
        return corpora;
    }

    @Override
    public List<DocumentSummary> documents(String tenantId) {
        Map<String, Object> body = Map.of(
                "size", 0,
                "aggs", Map.of("by_document", Map.of(
                        "terms", Map.of("field", "document_id", "size", 500),
                        "aggs", Map.of("first_chunk", Map.of("top_hits", Map.of(
                                "size", 1,
                                "sort", List.of(Map.of("ordinal", "asc")),
                                "_source", List.of("text")))))));
        JsonNode response;
        try {
            response = restClient.post()
                    .uri("/{index}/_search", INDEX_PREFIX + tenantId.toLowerCase())
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(body)
                    .retrieve()
                    .body(JsonNode.class);
        } catch (HttpClientErrorException.NotFound e) {
            return List.of();
        }
        List<DocumentSummary> documents = new ArrayList<>();
        for (JsonNode bucket : response.path("aggregations").path("by_document").path("buckets")) {
            String text = bucket.path("first_chunk").path("hits").path("hits")
                    .path(0).path("_source").path("text").asText();
            documents.add(new DocumentSummary(
                    bucket.path("key").asText(),
                    bucket.path("doc_count").asLong(),
                    text.length() > PREVIEW_CHARS ? text.substring(0, PREVIEW_CHARS) + "…" : text));
        }
        return documents;
    }

    private List<RetrievedChunk> search(String tenantId, Map<String, Object> body) {
        String index = "chunks-" + tenantId.toLowerCase();
        JsonNode response;
        try {
            response = restClient.post()
                    .uri("/{index}/_search", index)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(body)
                    .retrieve()
                    .body(JsonNode.class);
        } catch (HttpClientErrorException.NotFound e) {
            // Fresh tenant with nothing indexed yet — not an error.
            return List.of();
        }
        List<RetrievedChunk> results = new ArrayList<>();
        for (JsonNode hit : response.path("hits").path("hits")) {
            JsonNode source = hit.path("_source");
            results.add(new RetrievedChunk(
                    source.path("chunk_id").asText(),
                    source.path("document_id").asText(),
                    source.path("text").asText(),
                    hit.path("_score").asDouble()));
        }
        return results;
    }
}
