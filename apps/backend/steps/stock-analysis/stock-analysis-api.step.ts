import type { ApiRouteConfig, Handlers } from "motia";
import { z } from "zod";

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
