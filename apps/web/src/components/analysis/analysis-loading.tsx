"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { triggerAnalysis } from "@/lib/actions/analysis";
import { Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useStreamGroup } from "@motiadev/stream-client-react";

interface AnalysisLoadingProps {
  ticker: string;
}

export function AnalysisLoading({ ticker }: AnalysisLoadingProps) {
  const router = useRouter();
  const [traceId, setTraceId] = useState<string | null>(null);

  // Subscribe to stream events
  const { data: streamData = [] } = useStreamGroup<{
    id: string;
    symbol: string;
    status: string;
  }>({
    streamName: "stock-analysis-stream",
    groupId: "analysis",
  });

  // Derive everything from stream data
  const relevantEvent =
    traceId && streamData.length > 0
      ? streamData.find((item) => item.id === traceId)
      : null;

  const statusMessage = relevantEvent?.status || "Initializing analysis...";
  const isError =
    statusMessage.toLowerCase().includes("error") ||
    statusMessage.toLowerCase().includes("failed");

  // Trigger analysis on mount
  useEffect(() => {
    const startAnalysis = async () => {
      try {
        const result = await triggerAnalysis(ticker);

        if (result.status === "completed") {
          router.refresh();
        } else if (result.status === "processing") {
          setTraceId(result.traceId);
        }
      } catch (err) {
        // Check for NO_ACCESS error
        if (err instanceof Error) {
          try {
            const errorData = JSON.parse(err.message);
            if (errorData.code === "NO_ACCESS") {
              router.push("/dashboard/no-access");
              return;
            }
          } catch {
            // Not a JSON error, continue with default error handling
          }
        }
        // Error will be reflected in stream status from backend
        console.error("Failed to start analysis:", err);
      }
    };

    startAnalysis();
  }, [ticker, router]);

  // Check for completion
  useEffect(() => {
    if (statusMessage === "Analysis completed") {
      const timer = setTimeout(() => router.refresh(), 500);
      return () => clearTimeout(timer);
    }
  }, [statusMessage, router]);

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-6">
        <AlertCircle className="h-16 w-16 text-red-500" />
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-semibold text-red-600">
            Analysis Failed
          </h2>
          <p className="text-muted-foreground max-w-md">{statusMessage}</p>
        </div>
        <Button onClick={() => router.push("/")} variant="outline">
          Return to Home
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] space-y-6">
      <Loader2 className="h-12 w-12 animate-spin text-primary" />
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-semibold">
          Analyzing {ticker.toUpperCase()}
        </h2>
        <p className="text-sm text-muted-foreground animate-pulse min-h-5">
          {statusMessage}
        </p>
      </div>
      <div className="flex gap-3">
        <Button onClick={() => router.push("/dashboard")} variant="outline">
          View Dashboard
        </Button>
      </div>
      <p className="text-xs text-muted-foreground max-w-md text-center">
        Analysis is running in the background. You can navigate away and check
        progress on your dashboard.
      </p>
    </div>
  );
}
