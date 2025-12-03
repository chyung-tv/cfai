import { EventConfig, Handlers } from "motia";
import { rateStock } from "../lib/ai-functions/rating";
import { ProjectionSchema } from "../lib/ai-functions/projection-judge";
import z from "zod";
import { dcfResultSchema } from "./dcf.step";
import { qualitativeAnalysisSchema } from "./qualitative-analysis.step";
import { getValidatedState } from "../lib/statehooks";

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
  { logger, state, traceId, emit, streams }
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

  const projectionJudgeData = await getValidatedState(
    "projection-judge",
    ProjectionSchema,
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
    projectionJudgeData,
  };

  logger.info("Generating stock rating", { symbol, traceId });
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Gemini is generating stock rating...",
  });
  const rating = await rateStock(ratingInput);

  // store to state
  await state.set("stock-rating", traceId, rating);

  logger.info("Stock rating generated successfully", { symbol, traceId });
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Stock rating generated successfully.",
  });

  // emit event
  await emit({
    topic: "finish-stock-rating",
    data: {
      symbol,
    },
  });
};
