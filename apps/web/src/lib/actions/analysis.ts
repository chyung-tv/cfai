"use server";

import prisma from "@repo/db";
import type { PackedAnalysisData } from "@repo/types";
import { auth, getUserAccess } from "@/lib/auth";
import { redirect } from "next/navigation";

const CACHE_VALIDITY_DAYS = 5;

// Backend API URL
// Local: http://localhost:3001
// Production: https://your-project.motia.cloud (from Motia Cloud dashboard)
const BACKEND_API_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

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

  const symbol = ticker.toUpperCase();

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
    console.log(
      "[triggerAnalysis] Creating UserQuery for user:",
      session.user.id,
      "symbol:",
      symbol
    );
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
    console.log("[triggerAnalysis] Created UserQuery:", userQuery.id);

    return { status: "processing", traceId: data.traceId };
  } catch (error) {
    console.error("Error triggering analysis:", error);
    throw error;
  }
}

export async function forceRefreshAnalysis(ticker: string) {
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

  const symbol = ticker.toUpperCase();

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
    console.log(
      "[forceRefreshAnalysis] Creating UserQuery for user:",
      session.user.id,
      "symbol:",
      symbol
    );
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
    console.log("[forceRefreshAnalysis] Created UserQuery:", userQuery.id);

    return { status: "processing", traceId: data.traceId };
  } catch (error) {
    console.error("Error triggering analysis:", error);
    throw error;
  }
}
