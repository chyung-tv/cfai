"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type JsonObject = Record<string, unknown>;
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

function renderList(items: string[] | undefined) {
  if (!items || items.length === 0) return <p className="text-sm text-zinc-500">None</p>;
  return (
    <ul className="list-disc space-y-1 pl-5 text-sm">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function titleize(value: string) {
  return value
    .split("_")
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
}

function statusPillClass(state: WorkflowState | "idle") {
  if (state === "completed" || state === "completed_cached") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300";
  }
  if (state === "failed" || state === "cancelled") {
    return "border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300";
  }
  if (state === "running" || state === "queued") {
    return "border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-300";
  }
  return "border-zinc-200 bg-zinc-100 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300";
}

type CitationItem = {
  title?: string;
  url?: string;
  source?: string;
};

export default function AnalysisDemoPage() {
  const [symbol, setSymbol] = useState("AMD");
  const [loading, setLoading] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [payload, setPayload] = useState<JsonObject | null>(null);
  const [traceId, setTraceId] = useState<string | null>(null);
  const [liveEvents, setLiveEvents] = useState<WorkflowEvent[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  const structuredOutput = useMemo(
    () => (payload?.structuredOutput as JsonObject | undefined) ?? null,
    [payload],
  );
  const reportMarkdown = useMemo(
    () => (typeof payload?.reportMarkdown === "string" ? payload.reportMarkdown : null),
    [payload],
  );
  const citations = useMemo(
    () => (Array.isArray(payload?.citations) ? payload.citations : null),
    [payload],
  );
  const reverseDcf = useMemo(
    () => (payload?.reverseDcf as JsonObject | undefined) ?? null,
    [payload],
  );
  const auditGrowth = useMemo(
    () => (payload?.auditGrowthLikelihood as JsonObject | undefined) ?? null,
    [payload],
  );
  const advisorDecision = useMemo(
    () => (payload?.advisorDecision as JsonObject | undefined) ?? null,
    [payload],
  );
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
  const latestEvent = liveEvents[0] ?? null;
  const currentState: WorkflowState | "idle" = latestEvent?.state ?? "idle";
  const currentSubstate = latestEvent?.substate ?? null;
  const completedSteps = useMemo(() => {
    if (!currentSubstate) return new Set<string>();
    const idx = PIPELINE_STEPS.indexOf(currentSubstate);
    if (idx < 0) return new Set<string>();
    return new Set(PIPELINE_STEPS.slice(0, idx + 1));
  }, [currentSubstate]);

  async function loadLatestAnalysis() {
    const normalized = symbol.trim().toUpperCase();
    if (!normalized) {
      setError("Enter a symbol.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${BACKEND_URL}/analysis/latest?symbol=${encodeURIComponent(normalized)}`,
        { credentials: "include" },
      );
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

  function closeEventSource() {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }

  async function triggerAnalysis() {
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
      source.onmessage = async (event) => {
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

  return (
    <main className="min-h-screen bg-zinc-50 p-6 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <header className="sticky top-3 z-10 flex flex-col gap-4 rounded-xl border border-zinc-200 bg-white/95 p-5 shadow-sm backdrop-blur dark:border-zinc-800 dark:bg-zinc-900/95">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-semibold">Analysis Workbench</h1>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                Live SSE workflow + projection-backed result render from <code>/analysis/latest</code>.
              </p>
            </div>
            <span
              className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${statusPillClass(currentState)}`}
            >
              {currentSubstate ? `${currentState} / ${currentSubstate}` : currentState}
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            <input
              className="w-40 rounded border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="Symbol"
            />
            <button
              className="rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              onClick={triggerAnalysis}
              disabled={triggering}
            >
              {triggering ? "Triggering..." : "Trigger Workflow"}
            </button>
            <button
              className="rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              onClick={loadLatestAnalysis}
              disabled={loading}
            >
              {loading ? "Loading..." : "Refresh from DB"}
            </button>
          </div>

          <div className="space-y-2 rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
              Pipeline progress
            </p>
            <div className="grid gap-2 md:grid-cols-5">
              {PIPELINE_STEPS.map((step) => {
                const isActive = currentSubstate === step;
                const isComplete = completedSteps.has(step) || currentState === "completed";
                return (
                  <div
                    key={step}
                    className={`rounded border px-2 py-1 text-xs ${
                      isActive
                        ? "border-blue-300 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300"
                        : isComplete
                          ? "border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300"
                          : "border-zinc-200 bg-zinc-100 text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400"
                    }`}
                  >
                    {step}
                  </div>
                );
              })}
            </div>
          </div>

          {traceId ? (
            <p className="text-xs text-zinc-600 dark:text-zinc-400">
              traceId: <code>{traceId}</code>
            </p>
          ) : null}
          {error ? <p className="text-sm text-red-600 dark:text-red-400">{error}</p> : null}
        </header>

        <Card>
          <CardHeader>
            <CardTitle>Live Timeline</CardTitle>
            <CardDescription>Status and transition stream stays visible while reading results.</CardDescription>
          </CardHeader>
          <CardContent>
            {liveEvents.length === 0 ? (
              <p className="text-sm text-zinc-500 dark:text-zinc-400">No live events yet.</p>
            ) : (
              <div className="max-h-52 overflow-auto rounded border border-zinc-200 p-2 text-xs dark:border-zinc-800">
                {liveEvents.map((item, idx) => (
                  <div
                    key={`${item.id}-${item.state}-${item.substate ?? "none"}-${idx}`}
                    className="mb-1 rounded border border-zinc-200 px-2 py-1 dark:border-zinc-800"
                  >
                    <span className="font-semibold">[{item.state}]</span>{" "}
                    {item.substate ? <span className="text-zinc-500">({item.substate})</span> : null}{" "}
                    {item.message ?? ""}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {(loading || triggering) && !payload ? (
          <Card>
            <CardHeader>
              <CardTitle>Loading Analysis</CardTitle>
              <CardDescription>Building interactive result cards...</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="h-24 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800" />
                <div className="h-24 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800" />
                <div className="h-24 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800" />
                <div className="h-24 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800" />
              </div>
            </CardContent>
          </Card>
        ) : null}

        <Tabs defaultValue="overview">
          <TabsList className="w-full justify-start">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="deep-research">Deep Research</TabsTrigger>
            <TabsTrigger value="quant">Quant</TabsTrigger>
            <TabsTrigger value="decision">Decision</TabsTrigger>
            <TabsTrigger value="raw">Raw</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <Card>
              <CardHeader>
                <CardTitle>Overview</CardTitle>
                <CardDescription>Readable executive and business context snapshot.</CardDescription>
              </CardHeader>
              <CardContent>
                {structuredOutput ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
                      <p className="text-sm font-semibold">Executive Summary</p>
                      <p className="text-sm leading-6">
                        {String((structuredOutput as JsonObject)?.executiveSummary?.summary ?? "N/A")}
                      </p>
                      <p className="text-sm text-zinc-600 dark:text-zinc-400">
                        Lifeline: {String((structuredOutput as JsonObject)?.executiveSummary?.lifeline ?? "N/A")}
                      </p>
                    </div>
                    <div className="space-y-2 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
                      <p className="text-sm font-semibold">Management Profile</p>
                      <p className="text-sm leading-6">
                        {String((structuredOutput as JsonObject)?.managementProfile?.leadershipSummary ?? "N/A")}
                      </p>
                      <details>
                        <summary className="cursor-pointer text-sm font-semibold">Key People</summary>
                        <pre className="overflow-x-auto pt-2 text-xs">
                          {pretty((structuredOutput as JsonObject)?.managementProfile?.keyPeople ?? [])}
                        </pre>
                      </details>
                    </div>
                    <div className="space-y-2 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
                      <p className="text-sm font-semibold">Business Quality</p>
                      <p className="text-sm">
                        Tier: {String((structuredOutput as JsonObject)?.businessQuality?.qualityTier ?? "N/A")}
                      </p>
                      <p className="text-sm font-semibold">Moat</p>
                      {renderList(((structuredOutput as JsonObject)?.businessQuality?.moat as string[]) ?? [])}
                    </div>
                    <div className="space-y-2 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
                      <p className="text-sm font-semibold">Industry Profile</p>
                      <p className="text-sm">
                        Market Structure: {String((structuredOutput as JsonObject)?.industryProfile?.marketStructure ?? "N/A")}
                      </p>
                      <p className="text-sm">
                        Position: {String((structuredOutput as JsonObject)?.industryProfile?.position ?? "N/A")}
                      </p>
                      <p className="text-sm leading-6">
                        {String((structuredOutput as JsonObject)?.industryProfile?.positionRationale ?? "N/A")}
                      </p>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">No overview data yet.</p>
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
                    {reportMarkdown ?? "null"}
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
                    <p className="text-sm text-zinc-500 dark:text-zinc-400">No citations available.</p>
                  ) : (
                    <div className="grid gap-3 md:grid-cols-2">
                      {topCitationItems.map((item, idx) => (
                        <div
                          key={`${item.title ?? "citation"}-${idx}`}
                          className="rounded border border-zinc-200 p-3 text-sm dark:border-zinc-800"
                        >
                          <p className="font-medium">{item.title ?? "Untitled citation"}</p>
                          <p className="text-xs text-zinc-500 dark:text-zinc-400">{item.source ?? "Unknown source"}</p>
                          {item.url ? (
                            <a
                              className="text-xs text-blue-600 hover:underline dark:text-blue-400"
                              href={item.url}
                              target="_blank"
                              rel="noreferrer"
                            >
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
                        <div className="rounded-lg border border-zinc-200 p-3 text-sm dark:border-zinc-800">
                          <p className="text-zinc-500 dark:text-zinc-400">Optimistic CAGR</p>
                          <p className="text-lg font-semibold">
                            {String((reverseDcf as JsonObject)?.summary?.bestCaseRevenueCagrPct ?? "N/A")}%
                          </p>
                        </div>
                        <div className="rounded-lg border border-zinc-200 p-3 text-sm dark:border-zinc-800">
                          <p className="text-zinc-500 dark:text-zinc-400">Median CAGR</p>
                          <p className="text-lg font-semibold">
                            {String((reverseDcf as JsonObject)?.summary?.medianRevenueCagrPct ?? "N/A")}%
                          </p>
                        </div>
                        <div className="rounded-lg border border-zinc-200 p-3 text-sm dark:border-zinc-800">
                          <p className="text-zinc-500 dark:text-zinc-400">Conservative CAGR</p>
                          <p className="text-lg font-semibold">
                            {String((reverseDcf as JsonObject)?.summary?.worstCaseRevenueCagrPct ?? "N/A")}%
                          </p>
                        </div>
                      </div>
                      <details>
                        <summary className="cursor-pointer text-sm font-semibold">Scenario Grid</summary>
                        <pre className="max-h-[420px] overflow-auto pt-2 text-xs">
                          {pretty((reverseDcf as JsonObject)?.scenarioGrid ?? [])}
                        </pre>
                      </details>
                    </div>
                  ) : (
                    <p className="text-sm text-zinc-500 dark:text-zinc-400">No reverse DCF data yet.</p>
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
                    <p className="text-sm text-zinc-500 dark:text-zinc-400">No audit data yet.</p>
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
                          <div className="space-y-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
                            <p className="text-sm">
                              <span className="font-semibold">Required CAGR:</span>{" "}
                              {item.requiredRevenueCagrPct}% |{" "}
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
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">No advisor decision data yet.</p>
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
                        <div className="space-y-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
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
                                <div className="space-y-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
                                  <p className="text-sm">
                                    <span className="font-semibold">Required CAGR:</span>{" "}
                                    {caseItem.requiredRevenueCagrPct}% |{" "}
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
