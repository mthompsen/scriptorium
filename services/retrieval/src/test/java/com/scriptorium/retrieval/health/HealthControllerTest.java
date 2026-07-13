package com.scriptorium.retrieval.health;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Map;
import org.junit.jupiter.api.Test;

class HealthControllerTest {

    @Test
    void healthReportsOkWithServiceName() {
        Map<String, String> body = new HealthController().health();

        assertThat(body).containsEntry("status", "ok").containsEntry("service", "retrieval");
    }
}
