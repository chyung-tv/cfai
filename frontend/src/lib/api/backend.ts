const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:3001";

async function apiGet<T>(path: string, errorLabel = "Request"): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`${errorLabel} failed (${response.status})`);
  }
  return (await response.json()) as T;
}

async function apiPost<T>(path: string, body?: unknown, errorLabel = "Request"): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    method: "POST",
    credentials: "include",
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    throw new Error(`${errorLabel} failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export type PortfolioPositionRequest = {
  symbol: string;
  weight: number;
};

export const backendApi = {
  getPortfolioMetrics<T>(positions: PortfolioPositionRequest[]): Promise<T> {
    return apiPost<T>("/analysis/portfolio/metrics", { positions }, "Portfolio metrics");
  },
  getCandidateCards<T>(): Promise<T> {
    return apiGet<T>(
      "/analysis/candidates?sort_by=blended&quality_weight=0.4&portfolio_impact_weight=0.3&valuation_recent_weight=0.3&limit=120",
      "Candidate fetch",
    );
  },
  listSeedRuns<T>(): Promise<T> {
    return apiGet<T>("/api/v1/admin/maintenance/catalog/seed-runs", "Seed run fetch");
  },
  triggerSeedRun<T>(): Promise<T> {
    return apiPost<T>("/api/v1/admin/maintenance/catalog/seed/top-us-market-cap", undefined, "Seed trigger");
  },
  listCatalogStocks<T>(params: URLSearchParams): Promise<T> {
    return apiGet<T>(`/api/v1/admin/maintenance/catalog/stocks?${params.toString()}`, "Catalog fetch");
  },
  triggerAnalysis<T>(symbol: string, forceRefresh: boolean): Promise<T> {
    return apiPost<T>(`/analysis/trigger?force=${forceRefresh ? "true" : "false"}`, { symbol }, "Trigger");
  },
};

