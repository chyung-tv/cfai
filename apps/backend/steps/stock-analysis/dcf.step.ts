import { EventConfig, Handlers } from "motia";
import { performCustomDCF } from "../lib/functions/dcf";
import z from "zod";
import { getValidatedState } from "../lib/statehooks";
import { growthJudgementSchema } from "./judgement.step";
import { reverseDcfAnalysisSchema } from "./reverse-dcf.step";

const inputSchema = z.object({
  symbol: z.string(),
});

export const config: EventConfig = {
  name: "DCF",
  type: "event",
  description: "Process DCF with AI projections",
  subscribes: ["finish-growth-judgement"],
  emits: ["finish-dcf"],
  flows: ["stock-analysis-flow"],
  input: inputSchema,
};

export const handler: Handlers["DCF"] = async (
  input,
  { logger, state, emit, traceId, streams }
) => {
  const { symbol } = input;
  logger.info("Starting DCF processing for", { symbol });
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Calculating DCF from AI projections...",
  });

  // 1. Retrieve Growth Judgement (AI Assumptions)
  const judgement = await getValidatedState(
    "growth-judgement",
    growthJudgementSchema,
    state,
    traceId,
    logger
  );

  // 2. Retrieve Financial Data (from Reverse DCF step)
  const reverseDcfData = await getValidatedState(
    "reverse-dcf-analysis",
    reverseDcfAnalysisSchema,
    state,
    traceId,
    logger
  );

  const { dcfAssumptions } = judgement;
  const { revenueGrowthRates, terminalGrowthRate, discountRate } =
    dcfAssumptions;

  // 3. Bridge Logic: Expand 5-year AI projection to 10 years
  // Years 1-5: Explicit AI rates
  // Years 6-10: Linear fade to terminal rate
  const fullGrowthRates = [...revenueGrowthRates];
  const lastExplicitRate = revenueGrowthRates[4];

  for (let i = 1; i <= 5; i++) {
    const fadeStep = (lastExplicitRate - terminalGrowthRate) / 5;
    const fadedRate = lastExplicitRate - fadeStep * i;
    fullGrowthRates.push(fadedRate);
  }

  logger.info("Generated 10-year growth profile", { fullGrowthRates });

  // 4. Perform Base Case DCF
  const financials = {
    revenueTTM: reverseDcfData.ttmRevenue,
    fcfTTM: reverseDcfData.ttmFreeCashFlow,
    sharesOutstanding: reverseDcfData.sharesOutstanding,
    netDebt: reverseDcfData.netDebt,
  };

  const baseCaseResult = await performCustomDCF({
    symbol,
    aiParams: {
      revenueGrowthRates: fullGrowthRates,
      terminalGrowthRate,
      discountRate,
    },
    financials,
  });

  if (!baseCaseResult) {
    throw new Error("DCF Calculation failed");
  }

  // 5. Perform Sensitivity Analysis
  // Matrix: Discount Rate (+/- 1% in 0.5% steps) vs Terminal Growth (+/- 0.5% in 0.25% steps)
  const sensitivityMatrix: {
    terminalGrowthRates: number[];
    discountRates: number[];
    values: number[][];
  } = {
    terminalGrowthRates: [],
    discountRates: [],
    values: [],
  };

  // Define ranges
  const discountSteps = [-0.01, -0.005, 0, 0.005, 0.01]; // +/- 1%
  const terminalSteps = [-0.005, -0.0025, 0, 0.0025, 0.005]; // +/- 0.5%

  // Generate axes
  sensitivityMatrix.discountRates = discountSteps.map(
    (step) => discountRate + step
  );
  sensitivityMatrix.terminalGrowthRates = terminalSteps.map(
    (step) => terminalGrowthRate + step
  );

  // Calculate matrix
  for (const dRate of sensitivityMatrix.discountRates) {
    const row: number[] = [];
    for (const tRate of sensitivityMatrix.terminalGrowthRates) {
      const res = await performCustomDCF({
        symbol,
        aiParams: {
          revenueGrowthRates: fullGrowthRates, // Keep growth curve constant
          terminalGrowthRate: tRate,
          discountRate: dRate,
        },
        financials,
      });
      row.push(res ? res.intrinsicValuePerShare : 0);
    }
    sensitivityMatrix.values.push(row);
  }

  // 6. Save Result
  const finalResult = {
    ...baseCaseResult,
    sensitivity: sensitivityMatrix,
  };

  logger.info("Saving DCF result to state", { traceId });
  await state.set("dcf", traceId, finalResult);

  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "DCF calculation and sensitivity analysis completed.",
  });

  await emit({
    topic: "finish-dcf",
    data: {
      symbol,
    },
  });
};

// Re-export from shared types package
export { dcfResultSchema, type DCFResult } from "@repo/types";
