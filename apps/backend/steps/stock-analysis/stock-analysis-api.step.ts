import type { ApiRouteConfig, Handlers } from "motia";
import { z } from "zod";
import prisma from "@repo/db";

const stockQuerySchema = z.string().min(1);

export const config: ApiRouteConfig = {
  name: "StockAnalysisAPI",
  type: "api",
  path: "/stock/search",
  method: "GET",
  description: "Receives stock analysis request and emits event for processing",
  emits: ["process-stock-analysis"],
  flows: ["stock-analysis-flow"],
  responseSchema: {
    200: z.object({
      message: z.string(),
      status: z.string(),
      traceId: z.string(),
    }),
  },
};

export const handler: Handlers["StockAnalysisAPI"] = async (
  req,
  { emit, logger, traceId, streams }
) => {
  const { symbol } = req.queryParams;
  const parsedSymbol = stockQuerySchema.parse(symbol);

  logger.info(
    `StockAnalysis API endpoint called for ticker ${parsedSymbol}, trace ID: ${traceId}`
  );

  // 1. Check Cache (Freshness: 7 days)
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

  const cachedAnalysis = await prisma.analysis.findFirst({
    where: {
      symbol: parsedSymbol,
      createdAt: {
        gte: sevenDaysAgo,
      },
    },
    orderBy: {
      createdAt: "desc",
    },
  });

  if (cachedAnalysis) {
    logger.info(`Cache HIT for ${parsedSymbol}. Returning cached data.`, {
      traceId,
    });

    // 2. Cache Hit: Write directly to stream and RETURN (skip AI)
    await streams["stock-analysis-stream"].set("analysis", traceId, {
      id: traceId,
      symbol: parsedSymbol,
      status: "Completed (Cached)",
      data: cachedAnalysis.data as any, // Cast JSON to PackedAnalysisData
    });

    return {
      status: 200,
      body: {
        message: `Returning cached analysis for ${parsedSymbol}`,
        status: "completed",
        traceId,
      },
    };
  }

  // 3. Cache Miss: Emit event to start AI workflow
  logger.info(`Cache MISS for ${parsedSymbol}. Starting AI analysis.`, {
    traceId,
  });

  await emit({
    topic: "process-stock-analysis",
    data: {
      symbol: parsedSymbol,
    },
  });

  return {
    status: 200,
    body: {
      message: `Stock analysis request received for ${parsedSymbol}`,
      status: "processing",
      traceId,
    },
  };
};
