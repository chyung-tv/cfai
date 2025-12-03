import { EventConfig, Handlers } from "motia";
import { getValidatedState } from "../lib/statehooks";
import z from "zod";
import { prisma } from "../../lib/db";
import { qualitativeAnalysisSchema } from "./qualitative-analysis.step";
import { ProjectionSchema } from "../lib/ai-functions/projection-judge";
import { dcfResultSchema } from "./dcf.step";
import { ratingSchema } from "../lib/ai-functions/rating";
import { parseThesis } from "../lib/ai-functions/parseThesis";
import type { StockAnalysisStreamData } from "./stock-analysis.stream";

const inputSchema = z.object({
  symbol: z.string(),
});

export const config: EventConfig = {
  name: "return-db",
  type: "event",
  description: "Returns data to database",
  subscribes: ["finish-stock-rating"],
  emits: [],
  flows: ["stock-analysis-flow"],
  input: inputSchema,
};

export const handler: Handlers["return-db"] = async (
  input,
  { logger, state, traceId, streams }
) => {
  const { symbol } = input;
  logger.info("Retrieving and validating data from state", { traceId });
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Packing up data...",
  });
  const dcfData = await getValidatedState(
    "dcf",
    dcfResultSchema,
    state,
    traceId,
    logger
  );

  const { thesis } = await getValidatedState(
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

  const ratingData = await getValidatedState(
    "stock-rating",
    ratingSchema,
    state,
    traceId,
    logger
  );
  logger.info("All state data validated successfully", { traceId });
  logger.info("Parsing thesis", { traceId });
  const structuredThesis = await parseThesis(thesis);
  logger.info("Thesis parsed successfully", { traceId });
  logger.info("Packing data", { traceId });
  const packedData = {
    symbol,
    dcfData,
    structuredThesis,
    projectionJudgeData,
    ratingData,
  };

  // Save to database for caching
  logger.info("Saving analysis to database", { traceId });
  await prisma.analysis.create({
    data: {
      id: traceId,
      symbol,
      data: packedData as any, // Store as JSON
    },
  });
  logger.info("Analysis saved to database successfully", { traceId });

  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Analysis completed",
    data: packedData,
  });
  return;
};
