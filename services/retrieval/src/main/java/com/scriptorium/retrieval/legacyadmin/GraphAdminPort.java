package com.scriptorium.retrieval.legacyadmin;

import com.scriptorium.retrieval.legacyadmin.LegacyAdminModels.GraphStats;

/** Read-only graph statistics port for the legacy console (RP1: ISP). */
public interface GraphAdminPort {

    GraphStats graphStats(String tenantId);
}
