import type { EventConfig, Handlers } from "motia";
import { z } from "zod";
import { getValidatedState } from "../lib/statehooks";
import { qualitativeAnalysisSchema } from "./qualitative-analysis.step";
import { reverseDcfAnalysisSchema } from "./reverse-dcf.step";
import { evaluateGrowthFeasibility } from "../lib/ai-functions/judgement";

const inputSchema = z.object({
  symbol: z.string(),
});

export const config: EventConfig = {
  name: "ProcessGrowthJudgement",
  type: "event",
  description:
    "AI judges likelihood of achieving implied growth rates from reverse DCF based on qualitative analysis",
  subscribes: ["finish-reverse-dcf-analysis"],
  emits: ["finish-growth-judgement"],
  flows: ["stock-analysis-flow"],
  input: inputSchema,
};

export const handler: Handlers["ProcessGrowthJudgement"] = async (
  input,
  { logger, state, emit, traceId, streams }
) => {
  const { symbol } = input;

  logger.info("Processing growth judgement analysis", { symbol });

  // Stream to client
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Retrieving qualitative analysis and reverse DCF results...",
  });

  // Step 1: Retrieve qualitative analysis from state
  const qualitativeAnalysis = await getValidatedState(
    "stock-qualitative-analysis",
    qualitativeAnalysisSchema,
    state,
    traceId,
    logger
  );

  logger.info("Qualitative analysis retrieved", {
    hasThesis: !!qualitativeAnalysis.thesis,
    reasoningCount: qualitativeAnalysis.reasoning.length,
  });

  // Step 2: Retrieve reverse DCF results from state
  const reverseDcfAnalysis = await getValidatedState(
    "reverse-dcf-analysis",
    reverseDcfAnalysisSchema,
    state,
    traceId,
    logger
  );

  logger.info("Reverse DCF analysis retrieved", {
    impliedGrowthRatesCount: reverseDcfAnalysis.impliedGrowthRates.length,
    fcfMargin: reverseDcfAnalysis.fcfMargin,
    currentPrice: reverseDcfAnalysis.currentPrice,
  });

  // Step 3: Call AI judgement function
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "AI is judging the feasibility of implied growth rates...",
  });

  logger.info("Calling AI growth judgement function");

  const judgementResult = await evaluateGrowthFeasibility(
    qualitativeAnalysis,
    reverseDcfAnalysis
  );

  logger.info("AI judgement completed", {
    verdict: judgementResult.verdict,
    predictedCagr: judgementResult.independentPrediction.predictedCagr,
  });

  // Stream success
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Growth feasibility judgement completed.",
  });

  // Store judgement for downstream steps
  await state.set("growth-judgement", traceId, judgementResult);

  logger.info("State saved, emitting finish event");

  await emit({
    topic: "finish-growth-judgement",
    data: { symbol },
  });

  logger.info("Growth judgement step completed successfully");
};

// Re-export from shared types package
export { growthJudgementSchema, type GrowthJudgement } from "@repo/types";
