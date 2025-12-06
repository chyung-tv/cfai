"use server";

import prisma from "@repo/db";
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";

export async function getUserQueryHistory() {
  const session = await auth();
  if (!session?.user) {
    redirect("/login");
  }

  console.log("[getUserQueryHistory] Fetching for user:", session.user.id);

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

  console.log("[getUserQueryHistory] Found", queries.length, "queries");
  return queries;
}

export async function syncQueryStatus(queryId: string) {
  const session = await auth();
  if (!session?.user) {
    redirect("/login");
  }

  // Get the query
  const query = await prisma.userQuery.findUnique({
    where: {
      id: queryId,
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
        id: queryId,
      },
      data: {
        status: "completed",
        analysisResultId: analysisResult.id,
      },
    });

    return { status: "completed", analysisResultId: analysisResult.id };
  }

  return null;
}

export async function markQueryAsFailed(queryId: string) {
  const session = await auth();
  if (!session?.user) {
    redirect("/login");
  }

  await prisma.userQuery.update({
    where: {
      id: queryId,
      userId: session.user.id!, // Ensure user owns this query
    },
    data: {
      status: "failed",
    },
  });
}
