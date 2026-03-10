"use client";

import { useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type Position = {
  symbol: string;
  weight: number;
};

type StoredPortfolio = {
  version: number;
  positions: Position[];
};

type CandidateMeta = {
  status: "loading" | "ready" | "missing" | "error";
  isFresh: boolean | null;
};

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:3001";
const STORAGE_KEY = "cfai.portfolio.v1";
const STORAGE_VERSION = 1;
const DEFAULT_WEIGHT = 5;

const SEEDED_CANDIDATES = [
  { symbol: "AAPL", name: "Apple" },
  { symbol: "MSFT", name: "Microsoft" },
  { symbol: "NVDA", name: "NVIDIA" },
  { symbol: "AMZN", name: "Amazon" },
  { symbol: "GOOGL", name: "Alphabet" },
  { symbol: "META", name: "Meta Platforms" },
  { symbol: "TSLA", name: "Tesla" },
  { symbol: "BRK.B", name: "Berkshire Hathaway" },
  { symbol: "JPM", name: "JPMorgan Chase" },
  { symbol: "V", name: "Visa" },
  { symbol: "LLY", name: "Eli Lilly" },
  { symbol: "AVGO", name: "Broadcom" },
  { symbol: "WMT", name: "Walmart" },
  { symbol: "XOM", name: "Exxon Mobil" },
  { symbol: "MA", name: "Mastercard" },
  { symbol: "UNH", name: "UnitedHealth Group" },
  { symbol: "COST", name: "Costco" },
  { symbol: "JNJ", name: "Johnson & Johnson" },
  { symbol: "PG", name: "Procter & Gamble" },
  { symbol: "HD", name: "Home Depot" },
  { symbol: "ORCL", name: "Oracle" },
  { symbol: "MRK", name: "Merck" },
  { symbol: "ABBV", name: "AbbVie" },
  { symbol: "NFLX", name: "Netflix" },
  { symbol: "KO", name: "Coca-Cola" },
  { symbol: "PEP", name: "PepsiCo" },
  { symbol: "ADBE", name: "Adobe" },
  { symbol: "CRM", name: "Salesforce" },
  { symbol: "AMD", name: "Advanced Micro Devices" },
  { symbol: "CSCO", name: "Cisco" },
  { symbol: "BAC", name: "Bank of America" },
  { symbol: "MCD", name: "McDonald's" },
  { symbol: "TMO", name: "Thermo Fisher Scientific" },
  { symbol: "LIN", name: "Linde" },
  { symbol: "ACN", name: "Accenture" },
  { symbol: "INTU", name: "Intuit" },
  { symbol: "ABT", name: "Abbott Laboratories" },
  { symbol: "DIS", name: "Walt Disney" },
  { symbol: "QCOM", name: "Qualcomm" },
  { symbol: "VZ", name: "Verizon" },
  { symbol: "CMCSA", name: "Comcast" },
  { symbol: "TXN", name: "Texas Instruments" },
  { symbol: "NKE", name: "Nike" },
  { symbol: "DHR", name: "Danaher" },
  { symbol: "PM", name: "Philip Morris" },
  { symbol: "WFC", name: "Wells Fargo" },
  { symbol: "IBM", name: "IBM" },
  { symbol: "RTX", name: "RTX" },
  { symbol: "INTC", name: "Intel" },
  { symbol: "CAT", name: "Caterpillar" },
];

function formatWeight(value: number): string {
  return Number.isFinite(value) ? value.toFixed(1) : "0.0";
}

function readFreshness(payload: unknown): boolean | null {
  if (!payload || typeof payload !== "object") return null;
  const summary = (payload as { summary?: unknown }).summary;
  if (!summary || typeof summary !== "object") return null;
  const analysisFreshness = (summary as { analysisFreshness?: unknown }).analysisFreshness;
  if (!analysisFreshness || typeof analysisFreshness !== "object") return null;
  const isFresh = (analysisFreshness as { isFresh?: unknown }).isFresh;
  return typeof isFresh === "boolean" ? isFresh : null;
}

function freshnessBadge(meta: CandidateMeta): { label: string; variant: "default" | "secondary" | "outline" | "destructive" } {
  if (meta.status === "loading") return { label: "Checking cache...", variant: "outline" };
  if (meta.status === "error") return { label: "Lookup failed", variant: "destructive" };
  if (meta.status === "missing") return { label: "No cached analysis", variant: "secondary" };
  if (meta.isFresh === true) return { label: "Fresh (<=7d)", variant: "default" };
  if (meta.isFresh === false) return { label: "Stale (>7d)", variant: "secondary" };
  return { label: "Freshness unknown", variant: "outline" };
}

function getInitialPositions(): Position[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Partial<StoredPortfolio>;
    if (parsed.version !== STORAGE_VERSION || !Array.isArray(parsed.positions)) return [];
    return parsed.positions
      .filter((item): item is Position => typeof item?.symbol === "string" && typeof item?.weight === "number")
      .map((item) => ({ symbol: item.symbol, weight: Math.max(0, Math.min(100, item.weight)) }));
  } catch {
    return [];
  }
}

export default function PortfolioPage() {
  const [positions, setPositions] = useState<Position[]>(() => getInitialPositions());
  const [draggingOverPortfolio, setDraggingOverPortfolio] = useState(false);
  const [candidateMeta, setCandidateMeta] = useState<Record<string, CandidateMeta>>(
    Object.fromEntries(
      SEEDED_CANDIDATES.map((item) => [item.symbol, { status: "loading", isFresh: null } satisfies CandidateMeta]),
    ),
  );

  const totalWeight = useMemo(
    () => positions.reduce((acc, position) => acc + (Number.isFinite(position.weight) ? position.weight : 0), 0),
    [positions],
  );

  function upsertPosition(symbol: string): void {
    setPositions((current) => {
      if (current.some((item) => item.symbol === symbol)) return current;
      return [...current, { symbol, weight: DEFAULT_WEIGHT }];
    });
  }

  function removePosition(symbol: string): void {
    setPositions((current) => current.filter((item) => item.symbol !== symbol));
  }

  function updateWeight(symbol: string, nextWeight: number): void {
    const safeWeight = Number.isFinite(nextWeight) ? Math.max(0, Math.min(100, nextWeight)) : 0;
    setPositions((current) =>
      current.map((item) => {
        if (item.symbol !== symbol) return item;
        return { ...item, weight: safeWeight };
      }),
    );
  }

  useEffect(() => {
    const payload: StoredPortfolio = { version: STORAGE_VERSION, positions };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  }, [positions]);

  useEffect(() => {
    let cancelled = false;
    async function hydrateCandidates(): Promise<void> {
      await Promise.all(
        SEEDED_CANDIDATES.map(async (candidate) => {
          try {
            const response = await fetch(
              `${BACKEND_URL}/analysis/latest?symbol=${encodeURIComponent(candidate.symbol)}`,
              { credentials: "include" },
            );
            if (cancelled) return;
            if (!response.ok) {
              setCandidateMeta((current) => ({
                ...current,
                [candidate.symbol]: { status: "error", isFresh: null },
              }));
              return;
            }
            const data = (await response.json()) as unknown;
            if (cancelled) return;
            if (!data) {
              setCandidateMeta((current) => ({
                ...current,
                [candidate.symbol]: { status: "missing", isFresh: null },
              }));
              return;
            }
            setCandidateMeta((current) => ({
              ...current,
              [candidate.symbol]: { status: "ready", isFresh: readFreshness(data) },
            }));
          } catch {
            if (cancelled) return;
            setCandidateMeta((current) => ({
              ...current,
              [candidate.symbol]: { status: "error", isFresh: null },
            }));
          }
        }),
      );
    }
    void hydrateCandidates();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="min-h-screen bg-muted/20 px-4 py-5 md:px-6 md:py-6">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5">
        <header className="rounded-xl border bg-background p-4 shadow-sm md:p-5">
          <h1 className="text-xl font-semibold md:text-2xl">Portfolio Home</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Build a working portfolio quickly, then inspect candidate freshness before deeper analysis.
          </p>
        </header>

        <section className="grid gap-5 lg:grid-cols-[1.1fr_1.5fr]">
          <Card
            onDragOver={(event) => {
              event.preventDefault();
              setDraggingOverPortfolio(true);
            }}
            onDragLeave={() => setDraggingOverPortfolio(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDraggingOverPortfolio(false);
              const symbol = event.dataTransfer.getData("text/plain").trim().toUpperCase();
              if (!symbol) return;
              upsertPosition(symbol);
            }}
            className={draggingOverPortfolio ? "border-blue-500" : ""}
          >
            <CardHeader>
              <CardTitle>Portfolio Builder</CardTitle>
              <CardDescription>Drop candidate cards here to add with a default weight of 5%.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-lg border bg-muted/30 p-3 text-sm">
                <p className="font-medium">Total weight: {formatWeight(totalWeight)}%</p>
                <p className="text-muted-foreground">Edit each position weight between 0 and 100.</p>
              </div>

              {positions.length === 0 ? (
                <div className="rounded-lg border border-dashed p-5 text-sm text-muted-foreground">
                  Portfolio is empty. Drag a candidate from the right panel to start.
                </div>
              ) : (
                <div className="space-y-3">
                  {positions.map((position) => (
                    <div key={position.symbol} className="grid grid-cols-[1fr_auto_auto] items-center gap-2 rounded-lg border p-3">
                      <div>
                        <p className="font-semibold">{position.symbol}</p>
                        <p className="text-xs text-muted-foreground">Position weight</p>
                      </div>
                      <Input
                        type="number"
                        min={0}
                        max={100}
                        step={0.5}
                        value={position.weight}
                        onChange={(event) => updateWeight(position.symbol, Number(event.target.value))}
                        className="w-24"
                        aria-label={`${position.symbol} weight`}
                      />
                      <Button variant="outline" onClick={() => removePosition(position.symbol)}>
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Candidate Feed</CardTitle>
              <CardDescription>Seeded symbols render immediately; each card hydrates cache freshness from latest analysis.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {SEEDED_CANDIDATES.map((candidate) => {
                  const meta = candidateMeta[candidate.symbol] ?? { status: "loading", isFresh: null };
                  const freshness = freshnessBadge(meta);
                  return (
                    <div
                      key={candidate.symbol}
                      draggable
                      onDragStart={(event) => event.dataTransfer.setData("text/plain", candidate.symbol)}
                      className="cursor-grab rounded-lg border bg-background p-3 active:cursor-grabbing"
                    >
                      <div className="mb-2 flex items-start justify-between gap-2">
                        <div>
                          <p className="font-semibold">{candidate.symbol}</p>
                          <p className="text-xs text-muted-foreground">{candidate.name}</p>
                        </div>
                        <Badge variant={freshness.variant}>{freshness.label}</Badge>
                      </div>
                      <Button className="w-full" variant="outline" onClick={() => upsertPosition(candidate.symbol)}>
                        Add to Portfolio
                      </Button>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
}
