import type { ApiRouteConfig, Handlers } from "motia";
import { z } from "zod";
import { prisma } from "../../lib/db";

export const config: ApiRouteConfig = {
  name: "HistoryAPI",
  type: "api",
  path: "/api/history",
  method: "GET",
  description: "Returns the last 10 stock analysis records from the database",
  emits: [], // No events emitted by this endpoint,
  flows: ["stock-analysis-flow"],
  responseSchema: {
    200: z.array(
      z.object({
        id: z.string(),
        symbol: z.string(),
        createdAt: z.string(), // Dates are serialized as ISO strings in JSON
      })
    ),
  },
};

export const handler: Handlers["HistoryAPI"] = async (req, { logger }) => {
  logger.info("History API endpoint called");

  const analyses = await prisma.analysis.findMany({
    orderBy: {
      createdAt: "desc",
    },
    take: 10,
    select: {
      id: true,
      symbol: true,
      createdAt: true,
    },
  });

  const returnAnalyses = analyses.map((analysis) => ({
    id: analysis.id,
    symbol: analysis.symbol,
    createdAt: analysis.createdAt.toISOString(),
  }));

  return {
    status: 200,
    body: returnAnalyses,
  };
};
