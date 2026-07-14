package com.scriptorium.retrieval.legacyadmin;

import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.DocumentSummary;
import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.TenantCorpus;
import java.util.List;

/**
 * Read-only corpus administration port for the legacy console. Kept separate
 * from {@link com.scriptorium.retrieval.opensearch.SearchGateway} so the read
 * path's port stays focused on retrieval (interface segregation, RP1).
 */
public interface CorpusAdminPort {

    /** Every tenant chunk index with its chunk count. */
    List<TenantCorpus> tenantCorpora();

    /** Documents in one tenant's index, with chunk counts and a text preview. */
    List<DocumentSummary> documents(String tenantId);
}
