package com.scriptorium.retrieval.ollama;

import java.util.List;

/** Port for query embedding. */
public interface EmbeddingClient {

    List<Double> embed(String text);
}
