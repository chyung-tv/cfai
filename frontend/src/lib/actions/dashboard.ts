"use server";

import { z } from "zod";
import { logger } from "@/lib/logger";

// Query IDs are backend-defined during migration; accept non-empty string.
const queryIdSchema = z.string().min(1, "Invalid query ID format");

const BACKEND_API_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

export async function checkUserAccess(): Promise<boolean> {
  const response = await fetch(`${BACKEND_API_URL}/auth/me`, {
    method: "GET",
    cache: "no-store",
  });
  if (!response.ok) {
    return false;
  }
  const data = (await response.json()) as { canTriggerAnalysis?: boolean };
  return data.canTriggerAnalysis !== false;
}

export async function getUserQueryHistory() {
  logger.debug("Fetching user query history from backend");
  const response = await fetch(`${BACKEND_API_URL}/analysis/history`, {
    method: "GET",
    cache: "no-store",
  });
  if (!response.ok) {
    return [];
  }
  return response.json();
}

export async function syncQueryStatus(queryId: string) {
  const validatedId = queryIdSchema.parse(queryId);
  const response = await fetch(
    `${BACKEND_API_URL}/analysis/query/${validatedId}/sync`,
    {
      method: "GET",
      cache: "no-store",
    }
  );
  if (!response.ok) {
    return null;
  }
  return response.json();
}

export async function markQueryAsFailed(queryId: string) {
  const validatedId = queryIdSchema.parse(queryId);
  const response = await fetch(
    `${BACKEND_API_URL}/analysis/query/${validatedId}/mark-failed`,
    {
      method: "POST",
      cache: "no-store",
    }
  );
  if (!response.ok) {
    logger.warn("Failed to mark query as failed", { queryId: validatedId });
  }
}
