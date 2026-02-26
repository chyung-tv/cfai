import { useEffect, useMemo, useState } from "react";

export interface AnalysisStreamEvent {
  id: string;
  symbol: string;
  status: string;
  message?: string;
}

interface UseAnalysisStreamOptions {
  traceId?: string | null;
}

interface UseAnalysisStreamReturn {
  event: AnalysisStreamEvent | null;
  status: string;
  isError: boolean;
  allEvents: AnalysisStreamEvent[];
}

/**
 * Hook to subscribe to stock-analysis-stream and extract relevant event data
 * @param options - Configuration options
 * @param options.traceId - Optional trace ID to filter events for a specific analysis
 * @returns Object containing event data, status message, error state, and all events
 */
export function useAnalysisStream(
  options: UseAnalysisStreamOptions = {}
): UseAnalysisStreamReturn {
  const { traceId } = options;
  const [streamData, setStreamData] = useState<AnalysisStreamEvent[]>([]);

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

  useEffect(() => {
    let cancelled = false;

    const fetchEvents = async () => {
      try {
        const query = traceId ? `?traceId=${encodeURIComponent(traceId)}` : "";
        const response = await fetch(`${backendUrl}/analysis/events${query}`, {
          method: "GET",
          cache: "no-store",
        });
        if (!response.ok || cancelled) return;
        const data = (await response.json()) as { events?: AnalysisStreamEvent[] };
        setStreamData(data.events || []);
      } catch {
        // Ignore polling failures; UI will continue rendering last known state.
      }
    };

    fetchEvents();
    const interval = window.setInterval(fetchEvents, 2000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [backendUrl, traceId]);

  const event = useMemo(() => {
    if (!traceId || streamData.length === 0) return null;
    return streamData.find((item) => item.id === traceId) || null;
  });
  }, [traceId, streamData]);

  const status = event?.message || event?.status || "Initializing analysis...";
  const isError =
    status.toLowerCase().includes("error") ||
    status.toLowerCase().includes("failed");

  return {
    event,
    status,
    isError,
    allEvents: streamData,
  };
}
