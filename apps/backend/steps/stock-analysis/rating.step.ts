import { EventConfig, Handlers } from "motia";
import { rateStock } from "../lib/ai-functions/rating";
import { growthJudgementSchema } from "./judgement.step";
import z from "zod";
import { dcfResultSchema } from "./dcf.step";
import { qualitativeAnalysisSchema } from "./qualitative-analysis.step";
import { getValidatedState } from "../lib/statehooks";
import { publishAnalysisStatus } from "../../lib/status-stream";

const inputSchema = z.object({
  symbol: z.string(),
});

// Define validation schemas for state data

export const config: EventConfig = {
  name: "RateStock",
  type: "event",
  description: "Rating stock based on quantitative and qualitative analysis",
  subscribes: ["finish-dcf"],
  emits: ["finish-stock-rating"],
  flows: ["stock-analysis-flow"],
  input: inputSchema,
};

export const handler: Handlers["RateStock"] = async (
  input,
  { logger, state, traceId, emit }
) => {
  const { symbol } = input;
  logger.info("Retrieving and validating data from state", { traceId });

  // Use the reusable hook to get and validate all state data
  const dcfData = await getValidatedState(
    "dcf",
    dcfResultSchema,
    state,
    traceId,
    logger
  );

  const qualitativeAnalysisData = await getValidatedState(
    "stock-qualitative-analysis",
    qualitativeAnalysisSchema,
    state,
    traceId,
    logger
  );

  const growthJudgementData = await getValidatedState(
    "growth-judgement",
    growthJudgementSchema,
    state,
    traceId,
    logger
  );

  logger.info("All state data validated successfully", { traceId });

  // Use validated data (TypeScript now knows the exact types)
  const ratingInput = {
    symbol,
    dcfData,
    qualitativeAnalysisData,
    growthJudgementData,
  };

  logger.info("Generating stock rating", { symbol, traceId });
  await publishAnalysisStatus(traceId, symbol, "Gemini is generating stock rating...");
  const rating = await rateStock(ratingInput);
  await state.set("stock-rating", traceId, rating);
  logger.info("Stock rating generated successfully", { symbol, traceId });
  await publishAnalysisStatus(traceId, symbol, "Stock rating generated successfully.");

  // emit event
  await emit({
    topic: "finish-stock-rating",
    data: {
      symbol,
    },
  });
};
