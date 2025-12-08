"use server";

import prisma from "@repo/db";
import type { PackedAnalysisData } from "@repo/types";
import { auth, getUserAccess } from "@/lib/auth";
import { redirect } from "next/navigation";
import { z } from "zod";
import { logger } from "@/lib/logger";

const CACHE_VALIDITY_DAYS = 5;

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

export async function getAnalysis(
  ticker: string
): Promise<PackedAnalysisData | null> {
  // Validate and sanitize input
  const symbol = tickerSchema.parse(ticker);

  const analysis = await prisma.analysisResult.findFirst({
    where: {
      symbol: symbol,
    },
    orderBy: {
      createdAt: "desc",
    },
  });

  if (!analysis) {
    return null;
  }

  // Check if analysis is stale (older than CACHE_VALIDITY_DAYS)
  const ageInDays =
    (Date.now() - new Date(analysis.createdAt).getTime()) /
    (1000 * 60 * 60 * 24);

  if (ageInDays > CACHE_VALIDITY_DAYS) {
    // Cache miss: trigger new analysis in background and return null
    triggerAnalysis(ticker).catch((error) => {
      console.error("Failed to trigger background analysis:", error);
    });
    return null;
  }

  // Cache hit: return fresh data
  return analysis as unknown as PackedAnalysisData;
}

export async function triggerAnalysis(ticker: string) {
  // Validate and sanitize input
  const symbol = tickerSchema.parse(ticker);

  // Check authentication
  const session = await auth();
  if (!session?.user) {
    redirect("/login");
  }

  // Check access permission
  if (!getUserAccess(session)) {
    throw new Error(
      JSON.stringify({ code: "NO_ACCESS", message: "Beta access required" })
    );
  }

  logger.debug("Triggering analysis", { symbol, userId: session.user.id });

  // Check if we have a recent analysis (within CACHE_VALIDITY_DAYS)
  const existing = await prisma.analysisResult.findFirst({
    where: {
      symbol: symbol,
    },
    orderBy: {
      createdAt: "desc",
    },
  });

  if (existing) {
    const ageInDays =
      (Date.now() - new Date(existing.createdAt).getTime()) /
      (1000 * 60 * 60 * 24);

    if (ageInDays <= CACHE_VALIDITY_DAYS) {
      return { status: "completed", traceId: existing.id };
    }
  }

  // Check if there's already a processing request for this symbol (deduplication)
  const processingQuery = await prisma.userQuery.findFirst({
    where: {
      symbol: symbol,
      status: "processing",
    },
    orderBy: {
      createdAt: "desc",
    },
  });

  if (processingQuery && processingQuery.traceId) {
    logger.debug("Found existing processing query", {
      symbol,
      traceId: processingQuery.traceId,
    });
    // Return the existing trace ID so client can subscribe to its updates
    return { status: "processing", traceId: processingQuery.traceId };
  }

  // Call backend API
  try {
    const response = await fetch(
      `${BACKEND_API_URL}/stock/search?symbol=${symbol}`,
      {
        method: "GET",
        cache: "no-store",
      }
    );

    if (!response.ok) {
      throw new Error("Failed to trigger analysis");
    }

    const data = await response.json();

    // Create UserQuery to track this request
    logger.debug("Creating UserQuery", {
      userId: session.user.id,
      symbol,
      traceId: data.traceId,
    });
    const userQuery = await prisma.userQuery.create({
      data: {
        user: {
          connect: { id: session.user.id! },
        },
        symbol: symbol,
        status: "processing",
        traceId: data.traceId,
      },
    });
    logger.debug("UserQuery created", { queryId: userQuery.id });

    return { status: "processing", traceId: data.traceId };
  } catch (error) {
    logger.error("Error triggering analysis", { symbol, error });
    throw error;
  }
}

export async function forceRefreshAnalysis(ticker: string) {
  // Validate and sanitize input
  const symbol = tickerSchema.parse(ticker);

  // Check authentication
  const session = await auth();
  if (!session?.user) {
    redirect("/login");
  }

  // Check access permission
  if (!getUserAccess(session)) {
    throw new Error(
      JSON.stringify({ code: "NO_ACCESS", message: "Beta access required" })
    );
  }

  logger.debug("Force refreshing analysis", {
    symbol,
    userId: session.user.id,
  });

  // Always trigger a new analysis, regardless of cache
  try {
    const response = await fetch(
      `${BACKEND_API_URL}/stock/search?symbol=${symbol}`,
      {
        method: "GET",
        cache: "no-store",
      }
    );

    if (!response.ok) {
      throw new Error("Failed to trigger analysis");
    }

    const data = await response.json();

    // Create UserQuery to track this request
    logger.debug("Creating UserQuery for force refresh", {
      userId: session.user.id,
      symbol,
      traceId: data.traceId,
    });
    const userQuery = await prisma.userQuery.create({
      data: {
        user: {
          connect: { id: session.user.id! },
        },
        symbol: symbol,
        status: "processing",
        traceId: data.traceId,
      },
    });
    logger.debug("UserQuery created for force refresh", {
      queryId: userQuery.id,
    });

    return { status: "processing", traceId: data.traceId };
  } catch (error) {
    logger.error("Error force refreshing analysis", { symbol, error });
    throw error;
  }
}
