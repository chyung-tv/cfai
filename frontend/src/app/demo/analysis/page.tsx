"use client";

import { useMemo, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type JsonObject = Record<string, unknown>;
type WorkflowState = "queued" | "running" | "completed" | "failed" | "cancelled" | "completed_cached";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:3001";

function asRecord(value: unknown): JsonObject | null {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as JsonObject) : null;
}

function statusBadge(state: WorkflowState | "idle"): {
  variant: "default" | "secondary" | "destructive" | "outline";
  className?: string;
} {
  if (state === "completed" || state === "completed_cached") {
    return { variant: "default", className: "bg-emerald-600 text-white hover:bg-emerald-600" };
  }
  if (state === "failed" || state === "cancelled") return { variant: "destructive" };
  if (state === "queued" || state === "running") return { variant: "secondary" };
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
  if (isFresh === false) return { label: "Stale (>7d)", variant: "secondary" };
  return { label: "Freshness unknown", variant: "outline" };
}

export default function AnalysisDemoPage() {
  const [symbol, setSymbol] = useState("AMD");
  const [loading, setLoading] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [workflowState, setWorkflowState] = useState<WorkflowState | "idle">("idle");
  const [workflowSubstate, setWorkflowSubstate] = useState<string | null>(null);
  const [summaryFreshness, setSummaryFreshness] = useState<boolean | null>(null);

  const status = statusBadge(workflowState);
  const freshness = freshnessBadgeLabel(summaryFreshness);

  const statusLabel = useMemo(() => {
    if (!workflowSubstate) return workflowState;
    return `${workflowState} / ${workflowSubstate}`;
  }, [workflowState, workflowSubstate]);

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
      if (!response.ok) throw new Error(`Backend returned status ${response.status}`);
      const data = (await response.json()) as JsonObject | null;
      if (!data) {
        setWorkflowState("idle");
        setWorkflowSubstate("no_cached_analysis");
        setSummaryFreshness(null);
        setError(`No completed analysis found in DB for ${normalized}.`);
        return;
      }
      const freshness = asRecord(asRecord(data.summary)?.analysisFreshness);
      const isFresh = typeof freshness?.isFresh === "boolean" ? freshness.isFresh : null;
      setSummaryFreshness(isFresh);
      setWorkflowState("completed_cached");
      setWorkflowSubstate("latest_loaded");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown fetch error";
      setError(message);
      setWorkflowState("failed");
      setWorkflowSubstate("latest_fetch_failed");
    } finally {
      setLoading(false);
    }
  }

  async function triggerAnalysis(): Promise<void> {
    const normalized = symbol.trim().toUpperCase();
    if (!normalized) {
      setError("Enter a symbol.");
      return;
    }
    setTriggering(true);
    setError(null);
    setWorkflowState("running");
    setWorkflowSubstate("trigger_requested");
    try {
      const response = await fetch(`${BACKEND_URL}/analysis/trigger`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol: normalized }),
      });
      if (!response.ok) throw new Error(`Trigger failed with status ${response.status}`);
      setWorkflowState("queued");
      setWorkflowSubstate("trigger_accepted");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown trigger error";
      setError(message);
      setWorkflowState("failed");
      setWorkflowSubstate("trigger_failed");
    } finally {
      setTriggering(false);
    }
  }

  return (
    <main className="min-h-screen bg-muted/20 px-3 py-4 text-foreground md:px-6 md:py-6">
      <div className="mx-auto w-full max-w-4xl">
        <Card>
          <CardHeader>
            <CardTitle>Analysis Observation Lab (Internal)</CardTitle>
            <CardDescription>
              Internal controls for workflow trigger/refresh and status badge checks. Portfolio product flow lives on
              <code> /portfolio</code>.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
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

            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={status.variant} className={status.className}>
                {statusLabel}
              </Badge>
              <Badge variant={freshness.variant} className={freshness.className}>
                {freshness.label}
              </Badge>
            </div>

            {error ? (
              <Alert variant="destructive">
                <AlertTitle>Analysis error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
