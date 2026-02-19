/**
 * SSE status stream - publishes analysis status updates to Redis.
 * Replaces Motia WebSocket streams for task progress.
 * Clients connect via GET /analysis/:traceId/stream (proxied through Next.js).
 */

import { createClient } from "redis";

const CHANNEL_PREFIX = "analysis:status:";

let redisPublisher: ReturnType<typeof createClient> | null = null;

export interface AnalysisStatusEvent {
  traceId: string;
  symbol: string;
  status: string;
}

function getRedisUrl(): string {
  const url = process.env.REDIS_URL || "redis://localhost:6379";
  return url;
}

async function getPublisher() {
  if (!redisPublisher) {
    redisPublisher = createClient({ url: getRedisUrl() });
    redisPublisher.on("error", (err) => console.error("Redis publisher error:", err));
    await redisPublisher.connect();
  }
  return redisPublisher;
}

/**
 * Publish status update. Call this from analysis steps instead of streams.
 */
export async function publishAnalysisStatus(
  traceId: string,
  symbol: string,
  status: string
): Promise<void> {
  const redis = await getPublisher();
  const channel = `${CHANNEL_PREFIX}${traceId}`;
  const payload: AnalysisStatusEvent = { traceId, symbol, status };
  await redis.publish(channel, JSON.stringify(payload));
}

/**
 * Create a subscriber for status updates. Returns unsubscribe function.
 * Used by the GET /analysis/:traceId/stream endpoint.
 */
export async function createStatusSubscriber(
  traceId: string,
  onEvent: (event: AnalysisStatusEvent) => void
): Promise<() => Promise<void>> {
  const sub = createClient({ url: getRedisUrl() });
  sub.on("error", (err) => console.error("Redis subscriber error:", err));
  await sub.connect();

  const channel = `${CHANNEL_PREFIX}${traceId}`;
  await sub.subscribe(channel, (message) => {
    try {
      const event = JSON.parse(message) as AnalysisStatusEvent;
      onEvent(event);
    } catch {
      // ignore malformed
    }
  });

  return async () => {
    await sub.unsubscribe(channel);
    await sub.quit();
  };
}
