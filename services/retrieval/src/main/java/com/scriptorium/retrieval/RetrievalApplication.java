package com.scriptorium.retrieval;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Scriptorium retrieval service — the read path (ARCHITECTURE.md Section 7.3).
 *
 * <p>M0 stub: boots and serves /health. Hybrid retrieval lands in M2, graph queries in M4.
 */
@SpringBootApplication
public class RetrievalApplication {

    public static void main(String[] args) {
        SpringApplication.run(RetrievalApplication.class, args);
    }
}
