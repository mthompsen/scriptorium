package com.scriptorium.retrieval.legacyadmin;

import static org.assertj.core.api.Assertions.assertThat;

import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.DocumentSummary;
import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.GraphStats;
import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.TenantCorpus;
import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.TenantSummary;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.ui.ConcurrentModel;

class LegacyAdminControllerTest {

    private static final UUID TENANT = UUID.fromString("0f9a1c2e-3b4d-5e6f-8a9b-0c1d2e3f4a5b");

    private static final class FakeCorpus implements CorpusAdminPort {
        String lastTenant;

        @Override
        public List<TenantCorpus> tenantCorpora() {
            return List.of(new TenantCorpus(TENANT.toString(), 42));
        }

        @Override
        public List<DocumentSummary> documents(String tenantId) {
            lastTenant = tenantId;
            return List.of(new DocumentSummary("doc-1", 7, "Employees accrue PTO…"));
        }
    }

    private static final class FakeGraph implements GraphAdminPort {
        @Override
        public GraphStats graphStats(String tenantId) {
            return new GraphStats(8, 3);
        }
    }

    @Test
    void indexJoinsCorpusAndGraphStatsPerTenant() {
        LegacyAdminController controller =
                new LegacyAdminController(new FakeCorpus(), new FakeGraph());
        ConcurrentModel model = new ConcurrentModel();

        String view = controller.index(model);

        assertThat(view).isEqualTo("legacy/index");
        assertThat(model.getAttribute("tenants"))
                .asInstanceOf(org.assertj.core.api.InstanceOfAssertFactories.LIST)
                .containsExactly(new TenantSummary(TENANT.toString(), 42, 8, 3));
    }

    @Test
    void corpusViewCarriesDocumentsAndGraphStats() {
        FakeCorpus corpus = new FakeCorpus();
        LegacyAdminController controller = new LegacyAdminController(corpus, new FakeGraph());
        ConcurrentModel model = new ConcurrentModel();

        String view = controller.corpus(TENANT, model);

        assertThat(view).isEqualTo("legacy/corpus");
        assertThat(corpus.lastTenant).isEqualTo(TENANT.toString());
        assertThat(model.asMap())
                .containsEntry("tenantId", TENANT.toString())
                .containsEntry(
                        "documents",
                        List.of(new DocumentSummary("doc-1", 7, "Employees accrue PTO…")))
                .containsEntry("graphStats", new GraphStats(8, 3));
    }

    @Test
    void jsonApiExposesTheSameJoinedSummaries() {
        LegacyAdminController controller =
                new LegacyAdminController(new FakeCorpus(), new FakeGraph());

        List<TenantSummary> tenants = controller.tenants();

        assertThat(tenants).containsExactly(new TenantSummary(TENANT.toString(), 42, 8, 3));
    }
}
