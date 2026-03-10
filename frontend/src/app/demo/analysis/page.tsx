"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

type JsonObject = Record<string, unknown>;
type SummaryCardId = "businessQuality" | "valuationLegitimacy" | "investmentThesis";
type WorkflowState =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "completed_cached";

type WorkflowEvent = {
  id: string;
  symbol: string;
  state: WorkflowState;
  substate: string | null;
  message: string | null;
  payload: Record<string, unknown> | null;
};

type CaseItem = {
  caseName: "optimistic" | "median" | "conservative";
  requiredRevenueCagrPct: number;
  probabilityPct: number;
  likelihoodLabel: "likely" | "possible" | "unlikely";
  rationale: string;
  claimRefs: string[];
  risksToThesis: string[];
  supportingDrivers: string[];
};

type ProfileItem = {
  profile: "cash_preservation" | "balanced_compounder" | "capital_multiplier";
  profileSummary: string;
  caseAdvisories: Array<{
    caseName: "optimistic" | "median" | "conservative";
    requiredRevenueCagrPct: number;
    action: "accumulate" | "hold" | "trim" | "avoid";
    advice: string;
    reasoning: string;
    evidenceRefs: string[];
    keyRisks: string[];
    invalidateConditions: string[];
  }>;
};

type CitationItem = {
  title?: string;
  url?: string;
  source?: string;
};

type SummaryCard = {
  id: SummaryCardId;
  title: string;
  primary: string;
  secondary: string;
  supporting: string[];
  placeholder: boolean;
  score: number;
};

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:3001";
const PIPELINE_STEPS = [
  "validate_input",
  "resolve_query",
  "resolve_cache",
  "deep_research",
  "structured_output",
  "reverse_dcf",
  "audit_growth_likelihood",
  "advisor_decision",
  "publish_sse",
  "completed",
];

function pretty(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

function titleize(value: string): string {
  return value
    .split("_")
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
}

function asRecord(value: unknown): JsonObject | null {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as JsonObject) : null;
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

function asStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function renderList(items: string[]): JSX.Element {
  if (items.length === 0) return <p className="text-sm text-muted-foreground">No evidence listed.</p>;
  return (
    <ul className="list-disc space-y-1 pl-5 text-sm">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function statusBadge(state: WorkflowState | "idle"): {
  variant: "default" | "secondary" | "destructive" | "outline";
  className?: string;
} {
  if (state === "completed" || state === "completed_cached") {
    return { variant: "default", className: "bg-emerald-600 text-white hover:bg-emerald-600" };
  }
  if (state === "failed" || state === "cancelled") {
    return { variant: "destructive" };
  }
  if (state === "running" || state === "queued") {
    return { variant: "secondary" };
  }
  return { variant: "outline" };
}

function freshnessBadgeLabel(isFresh: boolean | null): {
  label: string;
  variant: "default" | "secondary" | "outline";
  className?: string;
} {
  if (isFresh === true) {
    return { label: "Fresh (<=7d)", variant: "default", className: "bg-emerald-600 text-white hover:bg-emerald-600" };
  }
  if (isFresh === false) {
    return { label: "Stale (>7d)", variant: "secondary" };
  }
  return { label: "Freshness unknown", variant: "outline" };
}

function getSummaryCards(payload: JsonObject | null, detailsPayload: JsonObject | null): SummaryCard[] {
  const summary = asRecord(payload?.summary);
  const details = asRecord(detailsPayload?.structuredOutput);
  const businessSummary = asRecord(summary?.businessQuality);
  const valuationSummary = asRecord(summary?.valuationLegitimacy);
  const thesisSummary = asRecord(summary?.investmentThesis);
  const detailBusiness = asRecord(details?.businessQuality);
  const detailExecutive = asRecord(details?.executiveSummary);

  const businessTier = asString(businessSummary?.tier) ?? asString(detailBusiness?.qualityTier);
  const moatStrength = asString(asRecord(businessSummary?.subfactors)?.moatStrength);
  const managementExecution = asString(asRecord(businessSummary?.subfactors)?.managementExecution);
  const industryPositioning = asString(asRecord(businessSummary?.subfactors)?.industryPositioning);
  const moatFallback = asStringList(detailBusiness?.moat)[0] ?? null;

  const valuationLabel = asString(valuationSummary?.label);
  const valuationBasis = asString(valuationSummary?.basis);
  const thesisText = asString(thesisSummary?.text) ?? asString(detailExecutive?.summary);

  const cards: SummaryCard[] = [
    {
      id: "businessQuality",
      title: "Business Quality",
      primary: businessTier ?? "Unavailable in current payload",
      secondary: businessTier ? "Tier from summary contract" : "Tier missing from summary and detail payload",
      supporting: [
        moatStrength ? `Moat strength: ${moatStrength}` : moatFallback ? `Moat signal: ${moatFallback}` : "",
        managementExecution ? `Management: ${managementExecution}` : "",
        industryPositioning ? `Industry: ${industryPositioning}` : "",
      ].filter(Boolean),
      placeholder: !businessTier,
      score: (businessTier ? 6 : 0) + (moatStrength || moatFallback ? 2 : 0) + (managementExecution ? 1 : 0),
    },
    {
      id: "valuationLegitimacy",
      title: "Valuation Legitimacy",
      primary: valuationLabel ?? "Unavailable in current payload",
      secondary: valuationBasis ?? "Valuation basis is missing from summary payload",
      supporting: valuationBasis ? [valuationBasis] : [],
      placeholder: !valuationLabel,
      score: (valuationLabel ? 5 : 0) + (valuationBasis ? 3 : 0),
    },
    {
      id: "investmentThesis",
      title: "Investment Thesis",
      primary: thesisText ?? "Unavailable in current payload",
      secondary: thesisText ? "Narrative extracted from summary/details" : "No summary thesis text was provided",
      supporting: [],
      placeholder: !thesisText,
      score: thesisText ? 7 : 0,
    },
  ];

  const basePriority: Record<SummaryCardId, number> = {
    businessQuality: 3,
    valuationLegitimacy: 2,
    investmentThesis: 1,
  };

  return cards.sort((left, right) => {
    if (left.score !== right.score) return right.score - left.score;
    return basePriority[right.id] - basePriority[left.id];
  });
}

export default function AnalysisDemoPage() {
  const [symbol, setSymbol] = useState("AMD");
  const [loading, setLoading] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [payload, setPayload] = useState<JsonObject | null>(null);
  const [traceId, setTraceId] = useState<string | null>(null);
  const [liveEvents, setLiveEvents] = useState<WorkflowEvent[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  const detailsPayload = useMemo(() => {
    const details = asRecord(payload?.details);
    return details ?? payload;
  }, [payload]);

  const structuredOutput = useMemo(() => asRecord(detailsPayload?.structuredOutput), [detailsPayload]);
  const reportMarkdown = useMemo(() => asString(detailsPayload?.reportMarkdown), [detailsPayload]);
  const citations = useMemo(() => (Array.isArray(detailsPayload?.citations) ? detailsPayload.citations : []), [detailsPayload]);
  const reverseDcf = useMemo(() => asRecord(detailsPayload?.reverseDcf), [detailsPayload]);
  const auditGrowth = useMemo(() => asRecord(detailsPayload?.auditGrowthLikelihood), [detailsPayload]);
  const advisorDecision = useMemo(() => asRecord(detailsPayload?.advisorDecision), [detailsPayload]);
  const summaryFreshness = useMemo(() => {
    const freshness = asRecord(asRecord(payload?.summary)?.analysisFreshness);
    return typeof freshness?.isFresh === "boolean" ? freshness.isFresh : null;
  }, [payload]);

  const auditCases = useMemo(() => {
    const maybe = auditGrowth?.cases;
    return Array.isArray(maybe) ? (maybe as CaseItem[]) : [];
  }, [auditGrowth]);
  const advisorProfiles = useMemo(() => {
    const maybe = advisorDecision?.profiles;
    return Array.isArray(maybe) ? (maybe as ProfileItem[]) : [];
  }, [advisorDecision]);
  const topCitationItems = useMemo(() => {
    if (!Array.isArray(citations)) return [];
    return citations.slice(0, 8) as CitationItem[];
  }, [citations]);

  const summaryCards = useMemo(() => getSummaryCards(payload, detailsPayload), [payload, detailsPayload]);
  const latestEvent = liveEvents[0] ?? null;
  const currentState: WorkflowState | "idle" = latestEvent?.state ?? "idle";
  const currentSubstate = latestEvent?.substate ?? null;
  const completedSteps = useMemo(() => {
    if (!currentSubstate) return new Set<string>();
    const idx = PIPELINE_STEPS.indexOf(currentSubstate);
    if (idx < 0) return new Set<string>();
    return new Set(PIPELINE_STEPS.slice(0, idx + 1));
  }, [currentSubstate]);

  async function loadLatestAnalysis(): Promise<void> {
    const normalized = symbol.trim().toUpperCase();
    if (!normalized) {
      setError("Enter a symbol.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BACKEND_URL}/analysis/latest?symbol=${encodeURIComponent(normalized)}`, {
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error(`Backend returned status ${response.status}`);
      }
      const data = (await response.json()) as JsonObject | null;
      if (!data) {
        setPayload(null);
        setError(`No completed analysis found in DB for ${normalized}.`);
        return;
      }
      setPayload(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown fetch error";
      setError(message);
      setPayload(null);
    } finally {
      setLoading(false);
    }
  }

  function closeEventSource(): void {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }

  async function triggerAnalysis(): Promise<void> {
    const normalized = symbol.trim().toUpperCase();
    if (!normalized) {
      setError("Enter a symbol.");
      return;
    }
    closeEventSource();
    setTriggering(true);
    setError(null);
    setPayload(null);
    setLiveEvents([]);
    setTraceId(null);
    try {
      const response = await fetch(`${BACKEND_URL}/analysis/trigger`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol: normalized }),
      });
      if (!response.ok) {
        throw new Error(`Trigger failed with status ${response.status}`);
      }
      const data = (await response.json()) as { traceId?: string };
      if (!data.traceId) {
        throw new Error("Trigger response did not include traceId");
      }
      setTraceId(data.traceId);
      const source = new EventSource(
        `${BACKEND_URL}/analysis/events/stream?traceId=${encodeURIComponent(data.traceId)}`,
        { withCredentials: true },
      );
      eventSourceRef.current = source;
      source.onmessage = async (event): Promise<void> => {
        try {
          const parsed = JSON.parse(event.data) as WorkflowEvent;
          setLiveEvents((prev) => [parsed, ...prev].slice(0, 50));
          if (parsed.state === "completed" || parsed.state === "completed_cached") {
            closeEventSource();
            await loadLatestAnalysis();
          } else if (parsed.state === "failed" || parsed.state === "cancelled") {
            closeEventSource();
          }
        } catch {
          // Ignore malformed SSE payloads and keep stream open.
        }
      };
      source.onerror = () => {
        closeEventSource();
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown trigger error";
      setError(message);
    } finally {
      setTriggering(false);
    }
  }

  useEffect(() => {
    return () => {
      closeEventSource();
    };
  }, []);

  const status = statusBadge(currentState);
  const freshness = freshnessBadgeLabel(summaryFreshness);

  return (
    <main className="min-h-screen bg-muted/20 px-3 py-4 text-foreground md:px-6 md:py-6">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-5">
        <header className="rounded-xl border bg-background p-4 shadow-sm md:p-5">
          <div className="space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h1 className="text-xl font-semibold md:text-2xl">Research Hub</h1>
                <p className="max-w-2xl text-sm text-muted-foreground">
                  Quality-first summary from <code>/analysis/latest</code>, with drill-down and live timeline.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={status.variant} className={status.className}>
                  {currentSubstate ? `${currentState} / ${currentSubstate}` : currentState}
                </Badge>
                <Badge variant={freshness.variant} className={freshness.className}>
                  {freshness.label}
                </Badge>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Input
                className="w-32 md:w-40"
                value={symbol}
                onChange={(event) => setSymbol(event.target.value)}
                placeholder="Symbol"
                aria-label="Symbol"
              />
              <Button onClick={triggerAnalysis} disabled={triggering}>
                {triggering ? "Triggering..." : "Trigger Workflow"}
              </Button>
              <Button variant="outline" onClick={loadLatestAnalysis} disabled={loading}>
                {loading ? "Loading..." : "Refresh from DB"}
              </Button>
            </div>

            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Pipeline progress</p>
              <div className="flex flex-wrap gap-1.5">
                {PIPELINE_STEPS.map((step) => {
                  const isActive = currentSubstate === step;
                  const isComplete = completedSteps.has(step) || currentState === "completed";
                  return (
                    <Badge
                      key={step}
                      variant={isActive ? "default" : isComplete ? "secondary" : "outline"}
                      className={cn(
                        "px-2 py-1 text-[11px]",
                        isActive ? "bg-blue-600 text-white hover:bg-blue-600" : "",
                      )}
                    >
                      {titleize(step)}
                    </Badge>
                  );
                })}
              </div>
            </div>

            {traceId ? (
              <p className="text-xs text-muted-foreground">
                traceId: <code>{traceId}</code>
              </p>
            ) : null}

            {error ? (
              <Alert variant="destructive">
                <AlertTitle>Analysis error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}
          </div>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>Summary Cards</CardTitle>
            <CardDescription>
              Cards reorder contextually by available signal quality. Missing fields show explicit placeholders.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {(loading || triggering) && !payload ? (
              <div className="grid gap-3 md:grid-cols-3">
                <Skeleton className="h-28 w-full rounded-lg" />
                <Skeleton className="h-28 w-full rounded-lg" />
                <Skeleton className="h-28 w-full rounded-lg" />
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-3">
                {summaryCards.map((card) => (
                  <Card key={card.id} className={cn(card.placeholder ? "border-dashed" : "")}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between gap-2">
                        <CardTitle className="text-base">{card.title}</CardTitle>
                        <Badge variant={card.placeholder ? "outline" : "secondary"}>
                          {card.placeholder ? "Partial" : "Complete"}
                        </Badge>
                      </div>
                      <CardDescription>{card.secondary}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <p className={cn("text-sm leading-6", card.placeholder ? "text-muted-foreground" : "text-foreground")}>
                        {card.primary}
                      </p>
                      {card.supporting.length > 0 ? (
                        <>
                          <Separator />
                          <ul className="list-disc space-y-1 pl-5 text-xs text-muted-foreground">
                            {card.supporting.map((item) => (
                              <li key={item}>{item}</li>
                            ))}
                          </ul>
                        </>
                      ) : null}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Live Timeline</CardTitle>
            <CardDescription>Status and transition stream stays visible while reading details.</CardDescription>
          </CardHeader>
          <CardContent>
            {liveEvents.length === 0 ? (
              <p className="text-sm text-muted-foreground">No live events yet.</p>
            ) : (
              <div className="max-h-52 overflow-auto rounded border p-2 text-xs">
                {liveEvents.map((item, idx) => (
                  <div key={`${item.id}-${item.state}-${item.substate ?? "none"}-${idx}`} className="mb-1 rounded border px-2 py-1">
                    <span className="font-semibold">[{item.state}]</span>{" "}
                    {item.substate ? <span className="text-muted-foreground">({item.substate})</span> : null}{" "}
                    {item.message ?? ""}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Tabs defaultValue="details">
          <TabsList className="h-auto w-full justify-start gap-1 overflow-x-auto whitespace-nowrap">
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="deep-research">Deep Research</TabsTrigger>
            <TabsTrigger value="quant">Quant</TabsTrigger>
            <TabsTrigger value="decision">Decision</TabsTrigger>
            <TabsTrigger value="raw">Raw</TabsTrigger>
          </TabsList>

          <TabsContent value="details">
            <Card>
              <CardHeader>
                <CardTitle>Business Detail</CardTitle>
                <CardDescription>Drill-down narrative and context from structured output.</CardDescription>
              </CardHeader>
              <CardContent>
                {structuredOutput ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2 rounded-lg border p-4">
                      <p className="text-sm font-semibold">Executive Summary</p>
                      <p className="text-sm leading-6">
                        {String(asRecord(structuredOutput.executiveSummary)?.summary ?? "Unavailable in current payload")}
                      </p>
                    </div>
                    <div className="space-y-2 rounded-lg border p-4">
                      <p className="text-sm font-semibold">Management Profile</p>
                      <p className="text-sm leading-6">
                        {String(
                          asRecord(structuredOutput.managementProfile)?.leadershipSummary ??
                            "Unavailable in current payload",
                        )}
                      </p>
                    </div>
                    <div className="space-y-2 rounded-lg border p-4">
                      <p className="text-sm font-semibold">Business Quality</p>
                      <p className="text-sm">
                        Tier: {String(asRecord(structuredOutput.businessQuality)?.qualityTier ?? "Unavailable in current payload")}
                      </p>
                      <p className="text-sm font-semibold">Moat</p>
                      {renderList(asStringList(asRecord(structuredOutput.businessQuality)?.moat))}
                    </div>
                    <div className="space-y-2 rounded-lg border p-4">
                      <p className="text-sm font-semibold">Industry Profile</p>
                      <p className="text-sm">
                        Market Structure:{" "}
                        {String(asRecord(structuredOutput.industryProfile)?.marketStructure ?? "Unavailable in current payload")}
                      </p>
                      <p className="text-sm">
                        Position: {String(asRecord(structuredOutput.industryProfile)?.position ?? "Unavailable in current payload")}
                      </p>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No detail data yet.</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="deep-research">
            <div className="grid gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Report</CardTitle>
                  <CardDescription>Full markdown report for detailed read-through.</CardDescription>
                </CardHeader>
                <CardContent>
                  <pre className="max-h-[520px] overflow-auto whitespace-pre-wrap text-xs">
                    {reportMarkdown ?? "Unavailable in current payload"}
                  </pre>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Top Citations</CardTitle>
                  <CardDescription>Quick source review without leaving the analysis flow.</CardDescription>
                </CardHeader>
                <CardContent>
                  {topCitationItems.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No citations available.</p>
                  ) : (
                    <div className="grid gap-3 md:grid-cols-2">
                      {topCitationItems.map((item, idx) => (
                        <div key={`${item.title ?? "citation"}-${idx}`} className="rounded border p-3 text-sm">
                          <p className="font-medium">{item.title ?? "Untitled citation"}</p>
                          <p className="text-xs text-muted-foreground">{item.source ?? "Unknown source"}</p>
                          {item.url ? (
                            <a className="text-xs text-blue-600 hover:underline dark:text-blue-400" href={item.url} target="_blank" rel="noreferrer">
                              Open source
                            </a>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="quant">
            <div className="grid gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Reverse DCF</CardTitle>
                  <CardDescription>Required CAGR profile and scenario grid.</CardDescription>
                </CardHeader>
                <CardContent>
                  {reverseDcf ? (
                    <div className="space-y-4">
                      <div className="grid gap-3 md:grid-cols-3">
                        <div className="rounded-lg border p-3 text-sm">
                          <p className="text-muted-foreground">Optimistic CAGR</p>
                          <p className="text-lg font-semibold">
                            {String(asRecord(reverseDcf.summary)?.bestCaseRevenueCagrPct ?? "N/A")}%
                          </p>
                        </div>
                        <div className="rounded-lg border p-3 text-sm">
                          <p className="text-muted-foreground">Median CAGR</p>
                          <p className="text-lg font-semibold">
                            {String(asRecord(reverseDcf.summary)?.medianRevenueCagrPct ?? "N/A")}%
                          </p>
                        </div>
                        <div className="rounded-lg border p-3 text-sm">
                          <p className="text-muted-foreground">Conservative CAGR</p>
                          <p className="text-lg font-semibold">
                            {String(asRecord(reverseDcf.summary)?.worstCaseRevenueCagrPct ?? "N/A")}%
                          </p>
                        </div>
                      </div>
                      <details>
                        <summary className="cursor-pointer text-sm font-semibold">Scenario Grid</summary>
                        <pre className="max-h-[420px] overflow-auto pt-2 text-xs">{pretty(reverseDcf.scenarioGrid ?? [])}</pre>
                      </details>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No reverse DCF data yet.</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Audit Growth Likelihood</CardTitle>
                  <CardDescription>Scenario-based probability and evidence review.</CardDescription>
                </CardHeader>
                <CardContent>
                  {auditCases.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No audit data yet.</p>
                  ) : (
                    <Tabs defaultValue={auditCases[0].caseName}>
                      <TabsList>
                        {auditCases.map((item) => (
                          <TabsTrigger key={item.caseName} value={item.caseName}>
                            {titleize(item.caseName)}
                          </TabsTrigger>
                        ))}
                      </TabsList>
                      {auditCases.map((item) => (
                        <TabsContent key={item.caseName} value={item.caseName}>
                          <div className="space-y-3 rounded-lg border p-4">
                            <p className="text-sm">
                              <span className="font-semibold">Required CAGR:</span> {item.requiredRevenueCagrPct}% |{" "}
                              <span className="font-semibold">Probability:</span> {item.probabilityPct}% |{" "}
                              <span className="font-semibold">Label:</span> {item.likelihoodLabel}
                            </p>
                            <p className="text-sm leading-6">{item.rationale}</p>
                            <div>
                              <p className="mb-1 text-sm font-semibold">Supporting Drivers</p>
                              {renderList(item.supportingDrivers)}
                            </div>
                            <div>
                              <p className="mb-1 text-sm font-semibold">Risks to Thesis</p>
                              {renderList(item.risksToThesis)}
                            </div>
                            <div>
                              <p className="mb-1 text-sm font-semibold">Evidence Refs</p>
                              {renderList(item.claimRefs)}
                            </div>
                          </div>
                        </TabsContent>
                      ))}
                    </Tabs>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="decision">
            <Card>
              <CardHeader>
                <CardTitle>Advisor Decision</CardTitle>
                <CardDescription>Profile-based recommendations with nested scenario tabs.</CardDescription>
              </CardHeader>
              <CardContent>
                {advisorProfiles.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No advisor decision data yet.</p>
                ) : (
                  <Tabs defaultValue={advisorProfiles[0].profile}>
                    <TabsList>
                      {advisorProfiles.map((item) => (
                        <TabsTrigger key={item.profile} value={item.profile}>
                          {titleize(item.profile)}
                        </TabsTrigger>
                      ))}
                    </TabsList>
                    {advisorProfiles.map((item) => (
                      <TabsContent key={item.profile} value={item.profile}>
                        <div className="space-y-3 rounded-lg border p-4">
                          <p className="text-sm leading-6">{item.profileSummary}</p>
                          <Tabs defaultValue={item.caseAdvisories[0]?.caseName ?? "optimistic"}>
                            <TabsList>
                              {item.caseAdvisories.map((caseItem) => (
                                <TabsTrigger key={caseItem.caseName} value={caseItem.caseName}>
                                  {titleize(caseItem.caseName)}
                                </TabsTrigger>
                              ))}
                            </TabsList>
                            {item.caseAdvisories.map((caseItem) => (
                              <TabsContent key={caseItem.caseName} value={caseItem.caseName}>
                                <div className="space-y-3 rounded-lg border p-4">
                                  <p className="text-sm">
                                    <span className="font-semibold">Required CAGR:</span> {caseItem.requiredRevenueCagrPct}% |{" "}
                                    <span className="font-semibold">Action:</span> {caseItem.action}
                                  </p>
                                  <p className="text-sm font-medium">{caseItem.advice}</p>
                                  <p className="text-sm leading-6">{caseItem.reasoning}</p>
                                  <div>
                                    <p className="mb-1 text-sm font-semibold">Key Risks</p>
                                    {renderList(caseItem.keyRisks)}
                                  </div>
                                  <div>
                                    <p className="mb-1 text-sm font-semibold">Invalidate Conditions</p>
                                    {renderList(caseItem.invalidateConditions)}
                                  </div>
                                  <div>
                                    <p className="mb-1 text-sm font-semibold">Evidence Refs</p>
                                    {renderList(caseItem.evidenceRefs)}
                                  </div>
                                </div>
                              </TabsContent>
                            ))}
                          </Tabs>
                        </div>
                      </TabsContent>
                    ))}
                  </Tabs>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="raw">
            <Card>
              <CardHeader>
                <CardTitle>Raw Payload Inspector</CardTitle>
                <CardDescription>Debug-safe fallback when schema sections are partially available.</CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="max-h-[640px] overflow-auto text-xs">{pretty(payload)}</pre>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}
