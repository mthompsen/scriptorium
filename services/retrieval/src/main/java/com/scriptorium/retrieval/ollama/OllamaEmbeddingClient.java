package com.scriptorium.retrieval.ollama;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

/** Embeds the query with the same model ingestion used, so dimensions match. */
@Component
public class OllamaEmbeddingClient implements EmbeddingClient {

    private final RestClient restClient;
    private final String model;

    public OllamaEmbeddingClient(
            @Value("${scriptorium.ollama.url}") String baseUrl,
            @Value("${scriptorium.embed-model}") String model) {
        this.restClient = RestClient.builder().baseUrl(baseUrl).build();
        this.model = model;
    }

    @Override
    public List<Double> embed(String text) {
        JsonNode response = restClient.post()
                .uri("/api/embed")
                .contentType(MediaType.APPLICATION_JSON)
                .body(Map.of("model", model, "input", List.of(text)))
                .retrieve()
                .body(JsonNode.class);
        List<Double> embedding = new ArrayList<>();
        for (JsonNode value : response.path("embeddings").path(0)) {
            embedding.add(value.asDouble());
        }
        return embedding;
    }
}
