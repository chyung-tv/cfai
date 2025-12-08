"use server";

import prisma from "@repo/db";
import { auth, getUserAccess } from "@/lib/auth";
import { redirect } from "next/navigation";
import { z } from "zod";
import { logger } from "@/lib/logger";

// Input validation schemas
const queryIdSchema = z.string().uuid("Invalid query ID format");

export async function checkUserAccess(): Promise<boolean> {
  const session = await auth();
  if (!session?.user) {
    return false;
  }
  return getUserAccess(session);
}

export async function getUserQueryHistory() {
  const session = await auth();
  if (!session?.user) {
    redirect("/login");
  }

  logger.debug("Fetching user query history", { userId: session.user.id });

  const queries = await prisma.userQuery.findMany({
    where: {
      userId: session.user.id!,
    },
    include: {
      analysisResult: true,
    },
    orderBy: {
      createdAt: "desc",
    },
  });

  logger.debug("Query history fetched", {
    userId: session.user.id,
    count: queries.length,
  });
  return queries;
}

export async function syncQueryStatus(queryId: string) {
  // Validate input
  const validatedId = queryIdSchema.parse(queryId);

  const session = await auth();
  if (!session?.user) {
    redirect("/login");
  }

  // Get the query
  const query = await prisma.userQuery.findUnique({
    where: {
      id: validatedId,
      userId: session.user.id!, // Ensure user owns this query
    },
  });

  if (!query || query.status !== "processing") {
    return null;
  }

  // Check if AnalysisResult exists for this symbol
  const analysisResult = await prisma.analysisResult.findFirst({
    where: {
      symbol: query.symbol,
    },
    orderBy: {
      createdAt: "desc",
    },
  });

  if (analysisResult) {
    // Update query to link to the result
    await prisma.userQuery.update({
      where: {
        id: validatedId,
      },
      data: {
        status: "completed",
        analysisResultId: analysisResult.id,
      },
    });

    logger.debug("Query status synced to completed", {
      queryId: validatedId,
      analysisResultId: analysisResult.id,
    });
    return { status: "completed", analysisResultId: analysisResult.id };
  }

  return null;
}

export async function markQueryAsFailed(queryId: string) {
  // Validate input
  const validatedId = queryIdSchema.parse(queryId);

  const session = await auth();
  if (!session?.user) {
    redirect("/login");
  }

  await prisma.userQuery.update({
    where: {
      id: validatedId,
      userId: session.user.id!, // Ensure user owns this query
    },
    data: {
      status: "failed",
    },
  });

  logger.debug("Query marked as failed", { queryId: validatedId });
}
