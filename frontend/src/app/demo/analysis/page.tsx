"use client";

import { useMemo, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:3001";
type SeedRun = {
  id: string;
  status: string;
  expectedCount: number | null;
  selectedCount: number | null;
  insertedCount: number | null;
  updatedCount: number | null;
  startedAt: string | null;
  finishedAt: string | null;
};

type StockItem = {
  symbol: string;
  nameDisplay: string;
  sector: string | null;
  marketCap: number | null;
  isActive: boolean;
  selectionRank: number | null;
  updatedAt: string | null;
};

type BatchStatus = "idle" | "queued" | "running" | "succeeded" | "failed";
type BatchRow = { state: BatchStatus; traceId: string | null; error: string | null };
type AnalysisMode = "lightweight" | "deep";

function formatNumber(value: number | null): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

function formatDate(value: string | null): string {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "-";
  return parsed.toLocaleString();
}

function batchBadge(state: BatchStatus): { label: string; variant: "default" | "secondary" | "destructive" | "outline" } {
  if (state === "succeeded") return { label: "succeeded", variant: "default" };
  if (state === "failed") return { label: "failed", variant: "destructive" };
  if (state === "running") return { label: "running", variant: "secondary" };
  if (state === "queued") return { label: "queued", variant: "outline" };
  return { label: "idle", variant: "outline" };
}

async function runWithConcurrency(
  symbols: string[],
  maxConcurrency: number,
  worker: (symbol: string) => Promise<void>,
): Promise<void> {
  let nextIndex = 0;
  const poolSize = Math.max(1, Math.min(maxConcurrency, symbols.length || 1));
  const runners = Array.from({ length: poolSize }, async () => {
    while (true) {
      const currentIndex = nextIndex;
      nextIndex += 1;
      if (currentIndex >= symbols.length) return;
      await worker(symbols[currentIndex]);
    }
  });
  await Promise.all(runners);
}

export default function AnalysisDemoPage() {
  const [seedRuns, setSeedRuns] = useState<SeedRun[]>([]);
  const [seedLoading, setSeedLoading] = useState(false);
  const [seedTriggering, setSeedTriggering] = useState(false);
  const [seedError, setSeedError] = useState<string | null>(null);

  const [catalog, setCatalog] = useState<StockItem[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [catalogQuery, setCatalogQuery] = useState("");
  const [catalogActiveOnly, setCatalogActiveOnly] = useState(true);
  const [catalogLimit, setCatalogLimit] = useState(100);
  const [catalogTotal, setCatalogTotal] = useState(0);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);

  const [mode, setMode] = useState<AnalysisMode>("lightweight");
  const [forceRefresh, setForceRefresh] = useState(false);
  const [maxRuns, setMaxRuns] = useState(10);
  const [runningBatch, setRunningBatch] = useState(false);
  const [batchRows, setBatchRows] = useState<Record<string, BatchRow>>({});
  const [batchError, setBatchError] = useState<string | null>(null);

  const runQueue = useMemo(() => {
    const limit = Number.isFinite(maxRuns) ? Math.max(1, Math.floor(maxRuns)) : 1;
    return selectedSymbols.slice(0, limit);
  }, [selectedSymbols, maxRuns]);

  const batchSummary = useMemo(() => {
    const rows = Object.values(batchRows);
    return {
      queued: rows.filter((row) => row.state === "queued").length,
      running: rows.filter((row) => row.state === "running").length,
      succeeded: rows.filter((row) => row.state === "succeeded").length,
      failed: rows.filter((row) => row.state === "failed").length,
    };
  }, [batchRows]);

  async function loadSeedRuns(): Promise<void> {
    setSeedLoading(true);
    setSeedError(null);
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/admin/maintenance/catalog/seed-runs`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error(`Seed run fetch failed (${response.status})`);
      const data = (await response.json()) as { runs?: SeedRun[] };
      setSeedRuns(Array.isArray(data.runs) ? data.runs : []);
    } catch (err) {
      setSeedError(err instanceof Error ? err.message : "Unknown seed fetch error");
    } finally {
      setSeedLoading(false);
    }
  }

  async function triggerSeedRun(): Promise<void> {
    setSeedTriggering(true);
    setSeedError(null);
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/admin/maintenance/catalog/seed/top-us-market-cap`, {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) throw new Error(`Seed trigger failed (${response.status})`);
      await loadSeedRuns();
    } catch (err) {
      setSeedError(err instanceof Error ? err.message : "Unknown seed trigger error");
    } finally {
      setSeedTriggering(false);
    }
  }

  async function loadCatalog(): Promise<void> {
    setCatalogLoading(true);
    setCatalogError(null);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(catalogLimit));
      params.set("offset", "0");
      if (catalogQuery.trim()) params.set("query", catalogQuery.trim());
      if (catalogActiveOnly) params.set("is_active", "true");
      const response = await fetch(`${BACKEND_URL}/api/v1/admin/maintenance/catalog/stocks?${params.toString()}`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error(`Catalog fetch failed (${response.status})`);
      const data = (await response.json()) as { total?: number; stocks?: StockItem[] };
      const items = Array.isArray(data.stocks) ? data.stocks : [];
      setCatalog(items);
      setCatalogTotal(typeof data.total === "number" ? data.total : items.length);
      setSelectedSymbols((current) => current.filter((symbol) => items.some((item) => item.symbol === symbol)));
    } catch (err) {
      setCatalogError(err instanceof Error ? err.message : "Unknown catalog fetch error");
    } finally {
      setCatalogLoading(false);
    }
  }

  function toggleSelected(symbol: string): void {
    setSelectedSymbols((current) =>
      current.includes(symbol) ? current.filter((item) => item !== symbol) : [...current, symbol],
    );
  }

  function selectTopVisible(): void {
    setSelectedSymbols(catalog.slice(0, Math.max(1, Math.min(maxRuns, catalog.length))).map((item) => item.symbol));
  }

  function clearSelection(): void {
    setSelectedSymbols([]);
  }

  async function runMassUpdate(): Promise<void> {
    if (!runQueue.length) {
      setBatchError("Select one or more symbols.");
      return;
    }
    setBatchError(null);
    setRunningBatch(true);
    const initial: Record<string, BatchRow> = {};
    for (const symbol of runQueue) {
      initial[symbol] = { state: "queued", traceId: null, error: null };
    }
    setBatchRows(initial);

    const effectiveForce = forceRefresh || mode === "deep";
    try {
      await runWithConcurrency(runQueue, 3, async (symbol) => {
        setBatchRows((current) => ({
          ...current,
          [symbol]: { state: "running", traceId: current[symbol]?.traceId ?? null, error: null },
        }));
        try {
          const endpoint = `${BACKEND_URL}/analysis/trigger?force=${effectiveForce ? "true" : "false"}`;
          const response = await fetch(endpoint, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol }),
          });
          if (!response.ok) throw new Error(`Trigger failed (${response.status})`);
          const data = (await response.json()) as { traceId?: string };
          setBatchRows((current) => ({
            ...current,
            [symbol]: { state: "succeeded", traceId: data.traceId ?? null, error: null },
          }));
        } catch (err) {
          setBatchRows((current) => ({
            ...current,
            [symbol]: {
              state: "failed",
              traceId: null,
              error: err instanceof Error ? err.message : "Unknown trigger error",
            },
          }));
        }
      });
    } finally {
      setRunningBatch(false);
    }
  }

  const latestSeedRun = seedRuns[0] ?? null;

  return (
    <main className="min-h-screen bg-muted/20 px-3 py-4 text-foreground md:px-6 md:py-6">
      <div className="mx-auto w-full max-w-6xl space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Maintenance (Internal)</CardTitle>
            <CardDescription>
              Internal maintenance controls: fetch/catalog operations and mass analysis updates. Product path remains
              <code> /portfolio</code>.
            </CardDescription>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Fetch</CardTitle>
            <CardDescription>Seed or refresh the stock catalog from provider-backed maintenance workflow.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Button onClick={triggerSeedRun} disabled={seedTriggering}>
                {seedTriggering ? "Starting..." : "Run Top US Market Cap Seed"}
              </Button>
              <Button variant="outline" onClick={loadSeedRuns} disabled={seedLoading}>
                {seedLoading ? "Loading..." : "Refresh Seed Runs"}
              </Button>
            </div>
            {latestSeedRun ? (
              <div className="grid gap-2 text-sm md:grid-cols-4">
                <div>
                  <p className="text-muted-foreground">Latest Status</p>
                  <p className="font-medium">{latestSeedRun.status}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Selected / Expected</p>
                  <p className="font-medium">
                    {latestSeedRun.selectedCount ?? "-"} / {latestSeedRun.expectedCount ?? "-"}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Inserted / Updated</p>
                  <p className="font-medium">
                    {latestSeedRun.insertedCount ?? "-"} / {latestSeedRun.updatedCount ?? "-"}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Started</p>
                  <p className="font-medium">{formatDate(latestSeedRun.startedAt)}</p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No seed runs loaded yet.</p>
            )}
            {seedError ? (
              <Alert variant="destructive">
                <AlertTitle>Fetch error</AlertTitle>
                <AlertDescription>{seedError}</AlertDescription>
              </Alert>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Stock Catalogue</CardTitle>
            <CardDescription>Select stocks to run in batch analysis.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Input
                className="w-52"
                value={catalogQuery}
                onChange={(event) => setCatalogQuery(event.target.value)}
                placeholder="Search symbol or name"
                aria-label="Search symbol or name"
              />
              <Input
                className="w-28"
                type="number"
                min={1}
                max={500}
                value={catalogLimit}
                onChange={(event) => setCatalogLimit(Number(event.target.value) || 100)}
                aria-label="Catalog limit"
              />
              <label className="inline-flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={catalogActiveOnly}
                  onChange={(event) => setCatalogActiveOnly(event.target.checked)}
                  aria-label="Active only"
                />
                Active only
              </label>
              <Button variant="outline" onClick={loadCatalog} disabled={catalogLoading}>
                {catalogLoading ? "Loading..." : "Load Catalogue"}
              </Button>
              <Button variant="outline" onClick={selectTopVisible} disabled={!catalog.length}>
                Select Top Visible
              </Button>
              <Button variant="outline" onClick={clearSelection} disabled={!selectedSymbols.length}>
                Clear Selection
              </Button>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-sm">
              <Badge variant="outline">Loaded: {catalog.length}</Badge>
              <Badge variant="outline">Total: {catalogTotal}</Badge>
              <Badge variant="secondary">Selected: {selectedSymbols.length}</Badge>
            </div>

            <div className="max-h-80 overflow-auto rounded border border-border">
              <table className="w-full text-sm">
                <thead className="bg-muted/60 text-left">
                  <tr>
                    <th className="px-2 py-2">Select</th>
                    <th className="px-2 py-2">Symbol</th>
                    <th className="px-2 py-2">Name</th>
                    <th className="px-2 py-2">Sector</th>
                    <th className="px-2 py-2">Mkt Cap</th>
                    <th className="px-2 py-2">Rank</th>
                    <th className="px-2 py-2">Active</th>
                  </tr>
                </thead>
                <tbody>
                  {catalog.map((item) => (
                    <tr key={item.symbol} className="border-t border-border">
                      <td className="px-2 py-2">
                        <input
                          type="checkbox"
                          checked={selectedSymbols.includes(item.symbol)}
                          onChange={() => toggleSelected(item.symbol)}
                          aria-label={`Select ${item.symbol}`}
                        />
                      </td>
                      <td className="px-2 py-2 font-medium">{item.symbol}</td>
                      <td className="px-2 py-2">{item.nameDisplay}</td>
                      <td className="px-2 py-2">{item.sector ?? "-"}</td>
                      <td className="px-2 py-2">{formatNumber(item.marketCap)}</td>
                      <td className="px-2 py-2">{item.selectionRank ?? "-"}</td>
                      <td className="px-2 py-2">{item.isActive ? "yes" : "no"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {catalogError ? (
              <Alert variant="destructive">
                <AlertTitle>Catalogue error</AlertTitle>
                <AlertDescription>{catalogError}</AlertDescription>
              </Alert>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Mass Update Analysis</CardTitle>
            <CardDescription>Queue selected symbols and trigger analysis in controlled parallel batches.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <label className="text-sm">
                Mode
                <select
                  className="ml-2 rounded border border-border bg-background px-2 py-1 text-sm"
                  value={mode}
                  onChange={(event) => setMode(event.target.value as AnalysisMode)}
                  aria-label="Analysis mode"
                >
                  <option value="lightweight">lightweight</option>
                  <option value="deep">deep</option>
                </select>
              </label>
              <label className="inline-flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={forceRefresh}
                  onChange={(event) => setForceRefresh(event.target.checked)}
                  aria-label="Force refresh"
                />
                Force refresh
              </label>
              <label className="text-sm">
                Max runs
                <Input
                  className="ml-2 inline-flex w-20"
                  type="number"
                  min={1}
                  max={500}
                  value={maxRuns}
                  onChange={(event) => setMaxRuns(Number(event.target.value) || 1)}
                  aria-label="Max runs"
                />
              </label>
              <Button onClick={runMassUpdate} disabled={runningBatch || runQueue.length === 0}>
                {runningBatch ? "Running..." : "Run Mass Update"}
              </Button>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-sm">
              <Badge variant="outline">Queue size: {runQueue.length}</Badge>
              <Badge variant="outline">Parallel: 3</Badge>
              <Badge variant="default">Succeeded: {batchSummary.succeeded}</Badge>
              <Badge variant="destructive">Failed: {batchSummary.failed}</Badge>
              <Badge variant="secondary">Running: {batchSummary.running}</Badge>
              <Badge variant="outline">Queued: {batchSummary.queued}</Badge>
            </div>

            <div className="max-h-72 overflow-auto rounded border border-border">
              <table className="w-full text-sm">
                <thead className="bg-muted/60 text-left">
                  <tr>
                    <th className="px-2 py-2">Symbol</th>
                    <th className="px-2 py-2">State</th>
                    <th className="px-2 py-2">Trace Id</th>
                    <th className="px-2 py-2">Error</th>
                  </tr>
                </thead>
                <tbody>
                  {runQueue.map((symbol) => {
                    const row = batchRows[symbol] ?? { state: "idle", traceId: null, error: null };
                    const badge = batchBadge(row.state);
                    return (
                      <tr key={symbol} className="border-t border-border">
                        <td className="px-2 py-2 font-medium">{symbol}</td>
                        <td className="px-2 py-2">
                          <Badge variant={badge.variant}>{badge.label}</Badge>
                        </td>
                        <td className="px-2 py-2 font-mono text-xs">{row.traceId ?? "-"}</td>
                        <td className="px-2 py-2">{row.error ?? "-"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {batchError ? (
              <Alert variant="destructive">
                <AlertTitle>Mass update error</AlertTitle>
                <AlertDescription>{batchError}</AlertDescription>
              </Alert>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
