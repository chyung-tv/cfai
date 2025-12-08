import { useStreamGroup } from "@motiadev/stream-client-react";

export interface AnalysisStreamEvent {
  id: string;
  symbol: string;
  status: string;
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

  const { data: streamData = [] } = useStreamGroup<AnalysisStreamEvent>({
    streamName: "stock-analysis-stream",
    groupId: "analysis",
  });

  // Find relevant event for this traceId (if provided)
  const event =
    traceId && streamData.length > 0
      ? streamData.find((item) => item.id === traceId) || null
      : null;

  const status = event?.status || "Initializing analysis...";
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
