"use client";

import { useEffect, useState, useRef } from "react";

export interface AnalysisStreamEvent {
  traceId: string;
  symbol: string;
  status: string;
}

interface UseAnalysisStreamOptions {
  traceId?: string | null;
}

interface UseAnalysisStreamReturn {
  status: string;
  isError: boolean;
}

/**
 * Hook to subscribe to analysis status via SSE (proxied through Next.js).
 * Replaces WebSocket stream with Server-Sent Events.
 */
export function useAnalysisStream(
  options: UseAnalysisStreamOptions = {}
): UseAnalysisStreamReturn {
  const { traceId } = options;
  const [status, setStatus] = useState("Initializing analysis...");
  const [isError, setIsError] = useState(false);
  const completedRef = useRef(false);

  useEffect(() => {
    if (!traceId) {
      setStatus("Initializing analysis...");
      return;
    }

    completedRef.current = false;
    const url = `/api/analysis/${traceId}/stream`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as AnalysisStreamEvent;
        setStatus(data.status);
        if (data.status === "Analysis completed") {
          completedRef.current = true;
          eventSource.close();
        } else if (
          data.status.toLowerCase().includes("error") ||
          data.status.toLowerCase().includes("failed")
        ) {
          setIsError(true);
          eventSource.close();
        }
      } catch {
        // ignore malformed
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      if (!completedRef.current) {
        setIsError(true);
        setStatus("Connection lost");
      }
    };

    return () => {
      eventSource.close();
    };
  }, [traceId]);

  return { status, isError };
}
