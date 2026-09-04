package com.scriptorium.retrieval;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Scriptorium retrieval service — the read path (ARCHITECTURE.md Section 7.3).
 *
 * <p>Hosts hybrid retrieval, graph queries, and the legacy admin console.
 */
@SpringBootApplication
public class RetrievalApplication {

    public static void main(String[] args) {
        SpringApplication.run(RetrievalApplication.class, args);
    }
}
