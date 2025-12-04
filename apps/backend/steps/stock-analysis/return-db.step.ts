import { EventConfig, Handlers } from "motia";
import { getValidatedState } from "../lib/statehooks";
import z from "zod";
import { qualitativeAnalysisSchema } from "./qualitative-analysis.step";
import { growthJudgementSchema } from "./judgement.step";
import { dcfResultSchema } from "./dcf.step";
import { ratingSchema } from "../lib/ai-functions/rating";
import { parseThesis } from "../lib/ai-functions/parseThesis";
import { reverseDcfAnalysisSchema } from "./reverse-dcf.step";

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

  const growthJudgementData = await getValidatedState(
    "growth-judgement",
    growthJudgementSchema,
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

  const reverseDcfData = await getValidatedState(
    "reverse-dcf-analysis",
    reverseDcfAnalysisSchema,
    state,
    traceId,
    logger
  );

  logger.info("All state data validated successfully", { traceId });
  logger.info("Parsing thesis", { traceId });
  const structuredThesis = await parseThesis(thesis);
  logger.info("Thesis parsed successfully", { traceId });
  logger.info("Packing data", { traceId });

  // Construct the AnalysisResult object matching Prisma schema
  const analysisResult = {
    id: traceId,
    symbol,
    price: reverseDcfData.currentPrice,
    score: 0, // Placeholder
    tier: ratingData.tier.classification,
    moat: ratingData.economicMoat.primaryMoat,
    valuationStatus: growthJudgementData.verdict,
    thesis: structuredThesis,
    dcf: dcfData,
    financials: {
      revenue: reverseDcfData.ttmRevenue,
      netIncome: 0, // Not currently persisted in reverse-dcf state
      fcf: reverseDcfData.ttmFreeCashFlow,
      netDebt: reverseDcfData.netDebt,
    },
  };

  // save to db
  logger.info("Saving analysis result to database", { traceId });

  // Dynamic import to avoid initialization issues during build/typegen
  const { default: prisma } = await import("@repo/db");

  await prisma.analysisResult.create({
    data: {
      ...analysisResult,
      // Ensure JSON fields are correctly typed for Prisma
      thesis: analysisResult.thesis,
      dcf: analysisResult.dcf,
      financials: analysisResult.financials,
    } as any,
  });
  logger.info("Analysis result saved to database", { traceId });

  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Analysis completed",
    data: analysisResult,
  });
  return;
};
