"use server";

import type { PackedAnalysisData } from "@repo/types";
import { z } from "zod";
import { logger } from "@/lib/logger";

// Input validation schemas
const tickerSchema = z
  .string()
  .min(1, "Ticker symbol is required")
  .max(10, "Ticker symbol too long")
  .regex(/^[A-Z0-9]+$/, "Ticker symbol must be uppercase letters/numbers only")
  .transform((val) => val.toUpperCase());

// Backend API URL
// Local: http://localhost:3001
// Production: https://your-project.motia.cloud (from Motia Cloud dashboard)
const BACKEND_API_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

type TriggerResponse = { status: "processing" | "completed"; traceId: string };

export async function getAnalysis(
  ticker: string
): Promise<PackedAnalysisData | null> {
  const symbol = tickerSchema.parse(ticker);

  const response = await fetch(
    `${BACKEND_API_URL}/analysis/latest?symbol=${encodeURIComponent(symbol)}`,
    {
      method: "GET",
      cache: "no-store",
    }
  );
  if (!response.ok) {
    return null;
  }
  const analysis = await response.json();
  return (analysis as PackedAnalysisData) || null;
}

export async function triggerAnalysis(ticker: string) {
  const symbol = tickerSchema.parse(ticker);

  try {
    const response = await fetch(`${BACKEND_API_URL}/analysis/trigger`, {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol }),
    });

    if (!response.ok) {
      throw new Error("Failed to trigger analysis");
    }

    const data = (await response.json()) as TriggerResponse;
    logger.debug("Analysis trigger accepted", { symbol, traceId: data.traceId });
    return { status: data.status, traceId: data.traceId };
  } catch (error) {
    logger.error("Error triggering analysis", { symbol, error });
    throw error;
  }
}

export async function forceRefreshAnalysis(ticker: string) {
  const symbol = tickerSchema.parse(ticker);
  logger.debug("Force refreshing analysis", { symbol });

  try {
    const response = await fetch(
      `${BACKEND_API_URL}/analysis/trigger?force=true`,
      {
        method: "POST",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol }),
      }
    );

    if (!response.ok) {
      throw new Error("Failed to trigger analysis");
    }

    const data = (await response.json()) as TriggerResponse;
    return { status: data.status, traceId: data.traceId };
  } catch (error) {
    logger.error("Error force refreshing analysis", { symbol, error });
    throw error;
  }
}
