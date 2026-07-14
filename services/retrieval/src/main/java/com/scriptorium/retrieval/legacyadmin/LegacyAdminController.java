package com.scriptorium.retrieval.legacyadmin;

import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.DocumentSummary;
import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.GraphStats;
import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.TenantCorpus;
import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.TenantSummary;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

/**
 * Legacy admin console (ARCHITECTURE.md Sections 7.3 and 10, RP5).
 *
 * <p>Deliberately old-style: server-rendered JSP views with JSTL, Bootstrap
 * for layout, jQuery for in-page refresh against the small JSON API below.
 * Read-only corpus and tenant administration; mutations stay with the
 * services that own the data (ingestion/BFF).
 */
@Controller
public class LegacyAdminController {

    private final CorpusAdminPort corpus;
    private final GraphAdminPort graph;

    public LegacyAdminController(CorpusAdminPort corpus, GraphAdminPort graph) {
        this.corpus = corpus;
        this.graph = graph;
    }

    @GetMapping({"/legacy/admin", "/legacy/admin/"})
    public String index(Model model) {
        model.addAttribute("tenants", tenantSummaries());
        return "legacy/index";
    }

    @GetMapping("/legacy/admin/corpus")
    public String corpus(@RequestParam("tenant_id") UUID tenantId, Model model) {
        model.addAttribute("tenantId", tenantId.toString());
        model.addAttribute("documents", corpus.documents(tenantId.toString()));
        model.addAttribute("graphStats", graph.graphStats(tenantId.toString()));
        return "legacy/corpus";
    }

    @GetMapping("/legacy/admin/api/tenants")
    @ResponseBody
    public List<TenantSummary> tenants() {
        return tenantSummaries();
    }

    @GetMapping("/legacy/admin/api/corpus")
    @ResponseBody
    public List<DocumentSummary> corpusApi(@RequestParam("tenant_id") UUID tenantId) {
        return corpus.documents(tenantId.toString());
    }

    private List<TenantSummary> tenantSummaries() {
        return corpus.tenantCorpora().stream().map(this::withGraphStats).toList();
    }

    private TenantSummary withGraphStats(TenantCorpus tenant) {
        GraphStats stats = graph.graphStats(tenant.tenantId());
        return new TenantSummary(
                tenant.tenantId(),
                tenant.chunkCount(),
                stats.entityCount(),
                stats.relationCount());
    }
}
