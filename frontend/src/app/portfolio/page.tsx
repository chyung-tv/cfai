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

type CandidateCard = {
  symbol: string;
  name: string | null;
  sector: string | null;
  freshnessUpdatedAt: string | null;
  freshnessExpiresAt: string | null;
  isFresh: boolean | null;
  qualityScore: number | null;
  valuationSignal: string | null;
  recentChangeSignal: string | null;
  portfolioImpactSignal: string | null;
  expectedReturnRange: {
    lowPct: number;
    highPct: number;
  } | null;
  scores: {
    quality: number;
    valuation: number;
    recentChange: number;
    valuationRecent: number;
    portfolioImpact: number;
    blended: number;
    portfolioRisk: number;
  } | null;
  status: CandidateMeta["status"];
};

type CandidateCardsResponse = {
  cards?: Array<{
    symbol?: string;
    name?: string | null;
    sector?: string | null;
    freshnessUpdatedAt?: string | null;
    freshnessExpiresAt?: string | null;
    isFresh?: boolean | null;
    qualityScore?: number | null;
    valuationSignal?: string | null;
    recentChangeSignal?: string | null;
    portfolioImpactSignal?: string | null;
    expectedReturnRange?: {
      lowPct?: number;
      highPct?: number;
    } | null;
    scores?: {
      quality?: number;
      valuation?: number;
      recentChange?: number;
      valuationRecent?: number;
      portfolioImpact?: number;
      blended?: number;
      portfolioRisk?: number;
    } | null;
  }>;
};

type PortfolioMetrics = {
  portfolioRiskScore: number;
  expectedReturnRange: { lowPct: number; highPct: number };
  sectorConcentrationWarning: string | null;
};

type PortfolioMetricsResponse = {
  portfolioRiskScore?: number;
  expectedReturnRange?: {
    lowPct?: number;
    highPct?: number;
  } | null;
  sectorConcentrationWarning?: string | null;
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

function freshnessBadge(meta: CandidateMeta): { label: string; variant: "default" | "secondary" | "outline" | "destructive" } {
  if (meta.status === "loading") return { label: "Checking cache...", variant: "outline" };
  if (meta.status === "error") return { label: "Lookup failed", variant: "destructive" };
  if (meta.status === "missing") return { label: "No cached analysis", variant: "secondary" };
  if (meta.isFresh === true) return { label: "Fresh (<=7d)", variant: "default" };
  if (meta.isFresh === false) return { label: "Stale (>7d)", variant: "secondary" };
  return { label: "Freshness unknown", variant: "outline" };
}

function toCandidateCard(input: CandidateCardsResponse["cards"][number]): CandidateCard | null {
  if (!input || typeof input.symbol !== "string" || !input.symbol.trim()) return null;
  const range = input.expectedReturnRange;
  const scores = input.scores;
  return {
    symbol: input.symbol.trim().toUpperCase(),
    name: typeof input.name === "string" ? input.name : null,
    sector: typeof input.sector === "string" ? input.sector : null,
    freshnessUpdatedAt: typeof input.freshnessUpdatedAt === "string" ? input.freshnessUpdatedAt : null,
    freshnessExpiresAt: typeof input.freshnessExpiresAt === "string" ? input.freshnessExpiresAt : null,
    isFresh: typeof input.isFresh === "boolean" ? input.isFresh : null,
    qualityScore: typeof input.qualityScore === "number" ? input.qualityScore : null,
    valuationSignal: typeof input.valuationSignal === "string" ? input.valuationSignal : null,
    recentChangeSignal: typeof input.recentChangeSignal === "string" ? input.recentChangeSignal : null,
    portfolioImpactSignal: typeof input.portfolioImpactSignal === "string" ? input.portfolioImpactSignal : null,
    expectedReturnRange:
      range && typeof range.lowPct === "number" && typeof range.highPct === "number"
        ? { lowPct: range.lowPct, highPct: range.highPct }
        : null,
    scores:
      scores &&
      typeof scores.quality === "number" &&
      typeof scores.valuation === "number" &&
      typeof scores.recentChange === "number" &&
      typeof scores.valuationRecent === "number" &&
      typeof scores.portfolioImpact === "number" &&
      typeof scores.blended === "number" &&
      typeof scores.portfolioRisk === "number"
        ? {
            quality: scores.quality,
            valuation: scores.valuation,
            recentChange: scores.recentChange,
            valuationRecent: scores.valuationRecent,
            portfolioImpact: scores.portfolioImpact,
            blended: scores.blended,
            portfolioRisk: scores.portfolioRisk,
          }
        : null,
    status: "ready",
  };
}

function fallbackCandidates(): CandidateCard[] {
  return SEEDED_CANDIDATES.map((candidate) => ({
    symbol: candidate.symbol,
    name: candidate.name,
    sector: null,
    freshnessUpdatedAt: null,
    freshnessExpiresAt: null,
    isFresh: null,
    qualityScore: null,
    valuationSignal: null,
    recentChangeSignal: null,
    portfolioImpactSignal: null,
    expectedReturnRange: null,
    scores: null,
    status: "loading",
  }));
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

function defaultPortfolioMetrics(): PortfolioMetrics {
  return {
    portfolioRiskScore: 50,
    expectedReturnRange: { lowPct: 0, highPct: 0 },
    sectorConcentrationWarning: null,
  };
}

export default function PortfolioPage() {
  const [positions, setPositions] = useState<Position[]>(() => getInitialPositions());
  const [draggingOverPortfolio, setDraggingOverPortfolio] = useState(false);
  const [candidates, setCandidates] = useState<CandidateCard[]>(() => fallbackCandidates());
  const [candidateSearch, setCandidateSearch] = useState("");
  const [freshnessFilter, setFreshnessFilter] = useState<"all" | "fresh" | "stale">("all");

  const totalWeight = useMemo(
    () => positions.reduce((acc, position) => acc + (Number.isFinite(position.weight) ? position.weight : 0), 0),
    [positions],
  );
  const candidateBySymbol = useMemo(
    () => new Map(candidates.map((candidate) => [candidate.symbol, candidate])),
    [candidates],
  );
  const fallbackPortfolioMetrics = useMemo<PortfolioMetrics>(() => {
    if (positions.length === 0 || totalWeight <= 0) {
      return defaultPortfolioMetrics();
    }
    let weightedRisk = 0;
    let weightedLow = 0;
    let weightedHigh = 0;
    const sectorWeights = new Map<string, number>();
    for (const position of positions) {
      const normalizedWeight = Math.max(0, position.weight) / totalWeight;
      const candidate = candidateBySymbol.get(position.symbol);
      const risk = candidate?.scores?.portfolioRisk ?? 0.5;
      const low = candidate?.expectedReturnRange?.lowPct ?? -1;
      const high = candidate?.expectedReturnRange?.highPct ?? 7;
      weightedRisk += normalizedWeight * risk;
      weightedLow += normalizedWeight * low;
      weightedHigh += normalizedWeight * high;
      const sector = candidate?.sector?.trim() || "Unknown";
      sectorWeights.set(sector, (sectorWeights.get(sector) ?? 0) + normalizedWeight);
    }
    let sectorConcentrationWarning: string | null = null;
    let topSector = "Unknown";
    let topWeight = 0;
    for (const [sector, weight] of sectorWeights.entries()) {
      if (weight > topWeight) {
        topSector = sector;
        topWeight = weight;
      }
    }
    if (topWeight >= 0.4) {
      sectorConcentrationWarning = `${topSector} concentration is high (${Math.round(topWeight * 100)}%).`;
    }
    return {
      portfolioRiskScore: Math.round(weightedRisk * 100),
      expectedReturnRange: {
        lowPct: Number(weightedLow.toFixed(1)),
        highPct: Number(weightedHigh.toFixed(1)),
      },
      sectorConcentrationWarning,
    };
  }, [candidateBySymbol, positions, totalWeight]);
  const [portfolioMetrics, setPortfolioMetrics] = useState<PortfolioMetrics>(() => defaultPortfolioMetrics());
  const displayedCandidates = useMemo(() => {
    const query = candidateSearch.trim().toUpperCase();
    return candidates.filter((candidate) => {
      if (freshnessFilter === "fresh" && candidate.isFresh !== true) return false;
      if (freshnessFilter === "stale" && candidate.isFresh !== false) return false;
      if (!query) return true;
      return candidate.symbol.includes(query) || (candidate.name ?? "").toUpperCase().includes(query);
    });
  }, [candidateSearch, candidates, freshnessFilter]);

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
    async function hydratePortfolioMetrics(): Promise<void> {
      if (positions.length === 0) {
        setPortfolioMetrics(defaultPortfolioMetrics());
        return;
      }
      try {
        const response = await fetch(`${BACKEND_URL}/analysis/portfolio/metrics`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ positions }),
        });
        if (cancelled) return;
        if (!response.ok) {
          setPortfolioMetrics(fallbackPortfolioMetrics);
          return;
        }
        const payload = (await response.json()) as PortfolioMetricsResponse;
        const range = payload.expectedReturnRange;
        if (
          typeof payload.portfolioRiskScore !== "number" ||
          !range ||
          typeof range.lowPct !== "number" ||
          typeof range.highPct !== "number"
        ) {
          setPortfolioMetrics(fallbackPortfolioMetrics);
          return;
        }
        setPortfolioMetrics({
          portfolioRiskScore: Math.round(payload.portfolioRiskScore),
          expectedReturnRange: {
            lowPct: Number(range.lowPct.toFixed(1)),
            highPct: Number(range.highPct.toFixed(1)),
          },
          sectorConcentrationWarning:
            typeof payload.sectorConcentrationWarning === "string" ? payload.sectorConcentrationWarning : null,
        });
      } catch {
        if (cancelled) return;
        setPortfolioMetrics(fallbackPortfolioMetrics);
      }
    }
    void hydratePortfolioMetrics();
    return () => {
      cancelled = true;
    };
  }, [fallbackPortfolioMetrics, positions]);

  useEffect(() => {
    let cancelled = false;
    async function hydrateCandidates(): Promise<void> {
      try {
        const response = await fetch(
          `${BACKEND_URL}/analysis/candidates?sort_by=blended&quality_weight=0.4&portfolio_impact_weight=0.3&valuation_recent_weight=0.3&limit=120`,
          { credentials: "include" },
        );
        if (cancelled) return;
        if (!response.ok) {
          setCandidates(fallbackCandidates().map((item) => ({ ...item, status: "error" })));
          return;
        }
        const payload = (await response.json()) as CandidateCardsResponse;
        if (cancelled) return;
        const parsedCards = (payload.cards ?? []).map(toCandidateCard).filter((item): item is CandidateCard => item !== null);
        if (parsedCards.length === 0) {
          setCandidates(fallbackCandidates().map((item) => ({ ...item, status: "missing" })));
          return;
        }
        setCandidates(parsedCards);
      } catch {
        if (cancelled) return;
        setCandidates(fallbackCandidates().map((item) => ({ ...item, status: "error" })));
      }
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
              <div className="grid gap-2 rounded-lg border bg-muted/30 p-3 text-sm md:grid-cols-2">
                <p className="font-medium">Total weight: {formatWeight(totalWeight)}%</p>
                <p className="text-muted-foreground">Edit each position weight between 0 and 100.</p>
                <p className="font-medium">Portfolio risk score: {portfolioMetrics.portfolioRiskScore}</p>
                <p className="font-medium">
                  Expected return range: {portfolioMetrics.expectedReturnRange.lowPct}% to{" "}
                  {portfolioMetrics.expectedReturnRange.highPct}%
                </p>
                <p className="text-muted-foreground md:col-span-2">
                  {portfolioMetrics.sectorConcentrationWarning ?? "Sector concentration is within heuristic threshold."}
                </p>
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
              <CardDescription>Blended ranking from cached projections with freshness badges and quick filters.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-col gap-2 md:flex-row">
                <Input
                  value={candidateSearch}
                  onChange={(event) => setCandidateSearch(event.target.value)}
                  placeholder="Search symbol or company"
                />
                <div className="flex gap-2">
                  <Button
                    variant={freshnessFilter === "all" ? "default" : "outline"}
                    onClick={() => setFreshnessFilter("all")}
                  >
                    All
                  </Button>
                  <Button
                    variant={freshnessFilter === "fresh" ? "default" : "outline"}
                    onClick={() => setFreshnessFilter("fresh")}
                  >
                    Fresh
                  </Button>
                  <Button
                    variant={freshnessFilter === "stale" ? "default" : "outline"}
                    onClick={() => setFreshnessFilter("stale")}
                  >
                    Stale
                  </Button>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {displayedCandidates.map((candidate) => {
                  const freshness = freshnessBadge({ status: candidate.status, isFresh: candidate.isFresh });
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
                          <p className="text-xs text-muted-foreground">
                            {candidate.name ?? "Unknown company"}
                            {candidate.sector ? ` · ${candidate.sector}` : ""}
                          </p>
                        </div>
                        <Badge variant={freshness.variant}>{freshness.label}</Badge>
                      </div>
                      <p className="mb-2 text-xs text-muted-foreground">
                        Blend {((candidate.scores?.blended ?? 0) * 100).toFixed(0)} · Risk{" "}
                        {((candidate.scores?.portfolioRisk ?? 0.5) * 100).toFixed(0)}
                      </p>
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
