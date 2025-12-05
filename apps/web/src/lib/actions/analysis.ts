"use server";

import prisma from "@repo/db";
import type { PackedAnalysisData } from "@repo/types";

export async function getAnalysis(
  ticker: string
): Promise<PackedAnalysisData | null> {
  const symbol = ticker.toUpperCase();

  const analysis = await prisma.analysisResult.findFirst({
    where: {
      symbol: symbol,
    },
    orderBy: {
      createdAt: "desc",
    },
  });

  // Cast to PackedAnalysisData (JSON fields are validated by Zod in backend)
  return analysis as PackedAnalysisData | null;
}

export async function triggerAnalysis(ticker: string) {
  const symbol = ticker.toUpperCase();

  // Check if we have a recent analysis (e.g., within 24 hours)
  // For now, we just check if it exists to avoid re-running
  const existing = await prisma.analysisResult.findFirst({
    where: {
      symbol: symbol,
    },
    orderBy: {
      createdAt: "desc",
    },
  });

  if (existing) {
    return { status: "completed", traceId: existing.id };
  }

  // Call backend API
  try {
    const response = await fetch(
      `http://localhost:3001/stock/search?symbol=${symbol}`,
      {
        method: "GET",
        cache: "no-store",
      }
    );

    if (!response.ok) {
      throw new Error("Failed to trigger analysis");
    }

    const data = await response.json();
    return { status: "processing", traceId: data.traceId };
  } catch (error) {
    console.error("Error triggering analysis:", error);
    throw error;
  }
}
