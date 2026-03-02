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
        <header className="flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <h1 className="text-2xl font-semibold">Analysis Demo</h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Trigger + SSE progress + final payload read from <code>/analysis/latest</code>.
          </p>
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
              {loading ? "Loading..." : "Load from DB"}
            </button>
          </div>
          {traceId ? (
            <p className="text-xs text-zinc-600 dark:text-zinc-400">
              traceId: <code>{traceId}</code>
            </p>
          ) : null}
          {liveEvents.length > 0 ? (
            <div className="max-h-40 overflow-auto rounded border border-zinc-200 p-2 text-xs dark:border-zinc-800">
              {liveEvents.map((item, idx) => (
                <p key={`${item.id}-${item.state}-${item.substate ?? "none"}-${idx}`}>
                  [{item.state}
                  {item.substate ? `/${item.substate}` : ""}] {item.message ?? ""}
                </p>
              ))}
            </div>
          ) : null}
          {error ? <p className="text-sm text-red-600 dark:text-red-400">{error}</p> : null}
        </header>

        <Card>
          <CardHeader>
            <CardTitle>Structured Output</CardTitle>
            <CardDescription>UI-ready summary sections parsed from deep research.</CardDescription>
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
                  <p className="text-sm font-semibold">Key People</p>
                  <pre className="overflow-x-auto text-xs">
                    {pretty((structuredOutput as JsonObject)?.managementProfile?.keyPeople ?? [])}
                  </pre>
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
                <div className="space-y-2 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800 md:col-span-2">
                  <p className="text-sm font-semibold">Recent Developments</p>
                  <pre className="overflow-x-auto text-xs">
                    {pretty((structuredOutput as JsonObject)?.recentDevelopments?.items ?? [])}
                  </pre>
                </div>
              </div>
            ) : (
              <pre className="overflow-x-auto text-xs">{pretty(structuredOutput)}</pre>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Reverse DCF</CardTitle>
            <CardDescription>10-year required CAGR matrix and summary from persisted payload.</CardDescription>
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
                <pre className="max-h-[420px] overflow-auto text-xs">
                  {pretty((reverseDcf as JsonObject)?.scenarioGrid ?? [])}
                </pre>
              </div>
            ) : (
              <pre className="overflow-x-auto text-xs">{pretty(reverseDcf)}</pre>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Audit Growth Likelihood</CardTitle>
            <CardDescription>Case-by-case view with tabs.</CardDescription>
          </CardHeader>
          <CardContent>
            {auditCases.length === 0 ? (
              <pre className="overflow-x-auto text-xs">{pretty(auditGrowth)}</pre>
            ) : (
              <Tabs defaultValue={auditCases[0].caseName}>
                <TabsList>
                  {auditCases.map((item) => (
                    <TabsTrigger key={item.caseName} value={item.caseName}>
                      {item.caseName}
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

        <Card>
          <CardHeader>
            <CardTitle>Advisor Decision</CardTitle>
            <CardDescription>Profile tabs with per-case recommendations (optimistic/median/conservative).</CardDescription>
          </CardHeader>
          <CardContent>
            {advisorProfiles.length === 0 ? (
              <pre className="overflow-x-auto text-xs">{pretty(advisorDecision)}</pre>
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
                              {caseItem.caseName}
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

        <Card>
          <CardHeader>
            <CardTitle>Deep Research (Full Markdown)</CardTitle>
            <CardDescription>Raw report persisted in DB.</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="max-h-[520px] overflow-auto whitespace-pre-wrap text-xs">
              {reportMarkdown ?? "null"}
            </pre>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Deep Research Citations</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-x-auto text-xs">{pretty(citations)}</pre>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
