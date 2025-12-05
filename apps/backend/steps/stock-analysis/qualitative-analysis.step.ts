import type { EventConfig, Handlers } from "motia";
import { z } from "zod";
import { qualitativeStockAnalysis } from "../lib/ai-functions/qualatative-analysis";

const inputSchema = z.object({
  symbol: z.string(),
});

export const config: EventConfig = {
  name: "ProcessStockAnalysis",
  type: "event",
  description: "Processes stock analysis in the background",
  subscribes: ["process-stock-analysis"],
  emits: ["finish-stock-qualitative-analysis"],
  flows: ["stock-analysis-flow"],
  input: inputSchema,
};

export const handler: Handlers["ProcessStockAnalysis"] = async (
  input,
  { logger, state, emit, traceId, streams }
) => {
  const { symbol } = input;

  logger.info("Processing comprehensive stock analysis", { symbol });

  // stream to client
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Gemini is analyzing the stock...",
  });

  // Generate comprehensive qualitative analysis (text-based)
  const { text: analysisThesis, reasoning } =
    await qualitativeStockAnalysis(symbol);

  logger.info(`Stock analysis completed for ${symbol}, storing in state...`, {
    traceId,
  });

  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Gemini has finished analyzing the stock.",
  });

  // Store full analysis thesis and reasoning for downstream steps
  await state.set("stock-qualitative-analysis", traceId, {
    symbol,
    thesis: analysisThesis,
    reasoning,
    generatedAt: new Date().toISOString(),
  });

  logger.info("store complete, emitting finish event...");

  await emit({
    topic: "finish-stock-qualitative-analysis",
    data: {
      symbol,
    },
  });

  logger.info("Event emitted successfully. Proceeding to next step");
};

// Re-export from shared types package
export {
  qualitativeAnalysisSchema,
  type QualitativeAnalysis,
} from "@repo/types";
