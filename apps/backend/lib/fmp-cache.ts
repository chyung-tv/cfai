/**
 * FMP API response cache in Redis.
 * Reduces external API calls: quotes 1h TTL, TTM financials 7d TTL.
 */

import { createClient } from "redis";

const QUOTE_TTL = 3600; // 1 hour
const TTM_TTL = 604800; // 7 days

let redis: ReturnType<typeof createClient> | null = null;

async function getRedis() {
  if (!redis) {
    redis = createClient({ url: process.env.REDIS_URL || "redis://localhost:6379" });
    redis.on("error", (err) => console.error("FMP cache Redis error:", err));
    await redis.connect();
  }
  return redis;
}

export async function getCachedQuote(symbol: string): Promise<unknown | null> {
  const client = await getRedis();
  const key = `fmp:quote:${symbol.toUpperCase()}`;
  const val = await client.get(key);
  return val ? JSON.parse(val) : null;
}

export async function setCachedQuote(symbol: string, data: unknown): Promise<void> {
  const client = await getRedis();
  const key = `fmp:quote:${symbol.toUpperCase()}`;
  await client.setEx(key, QUOTE_TTL, JSON.stringify(data));
}

export async function getCachedTtm(symbol: string): Promise<unknown | null> {
  const client = await getRedis();
  const key = `fmp:ttm:${symbol.toUpperCase()}`;
  const val = await client.get(key);
  return val ? JSON.parse(val) : null;
}

export async function setCachedTtm(symbol: string, data: unknown): Promise<void> {
  const client = await getRedis();
  const key = `fmp:ttm:${symbol.toUpperCase()}`;
  await client.setEx(key, TTM_TTL, JSON.stringify(data));
}
