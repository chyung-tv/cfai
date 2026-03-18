import { copilotClient } from "@/shared/api/copilot_client";
import { APP_CONFIG } from "@/lib/config";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? APP_CONFIG.backendUrl;

export const streamClient = {
  streamChatTurn: copilotClient.streamChatTurn,
  subscribeNotifications: (
    userId: string,
    handlers: {
      onMemoryWritten?: (payload: { memoryKey: string; memoryValue: string; threadId: string }) => void;
      onError?: (error: Event) => void;
    },
  ): (() => void) => {
    const url = `${BACKEND_URL}/copilot/notifications/stream?userId=${encodeURIComponent(userId)}`;
    const source = new EventSource(url, { withCredentials: true });
    source.addEventListener("memory_written", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as { memoryKey: string; memoryValue: string; threadId: string };
        handlers.onMemoryWritten?.(payload);
      } catch {
        // Ignore invalid SSE payload.
      }
    });
    source.addEventListener("error", (event) => {
      handlers.onError?.(event);
    });
    return () => source.close();
  },
};

