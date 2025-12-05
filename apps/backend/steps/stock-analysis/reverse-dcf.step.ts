import type { EventConfig, Handlers } from "motia";
import { z } from "zod";
import { fetchFinancialReportData } from "../lib/functions/ttmReport";
import { fetchQuote } from "../lib/functions/quote";
import {
  reverseDcf,
  reverseDcfResultSchema,
  type ReverseDcfResult,
} from "../lib/functions/reverse-dcf";

const inputSchema = z.object({
  symbol: z.string(),
});

export const config: EventConfig = {
  name: "ProcessReverseDcfAnalysis",
  type: "event",
  description: "Calculates reverse DCF analysis in the background",
  subscribes: ["finish-stock-qualitative-analysis"],
  emits: ["finish-reverse-dcf-analysis"],
  flows: ["stock-analysis-flow"],
  input: inputSchema,
};

export const handler: Handlers["ProcessReverseDcfAnalysis"] = async (
  input,
  { logger, state, emit, traceId, streams }
) => {
  const { symbol } = input;

  logger.info("Processing reverse DCF analysis", { symbol });

  // Stream to client
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Fetching current stock price and market data...",
  });

  // Step 1: Fetch quote data
  logger.info("Fetching quote data", { symbol });
  const quote = await fetchQuote(symbol);

  logger.info("Quote data fetched successfully", {
    price: quote.price,
    marketCap: quote.marketCap,
  });

  // Step 2: Fetch TTM financial reports
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Fetching trailing twelve months financial data...",
  });

  logger.info("Fetching TTM financial data");
  const financialData = await fetchFinancialReportData(symbol);

  if (!financialData) {
    logger.error("Failed to fetch TTM financial data", { symbol });
    throw new Error(`Failed to fetch financial data for ${symbol}`);
  }

  logger.info("TTM financial data fetched successfully");

  // Step 3: Parse inputs for reverse DCF
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Calculating implied growth rates across discount rates...",
  });

  const ttmRevenue = financialData.incomeStatement.revenue as number;
  const ttmFreeCashFlow = financialData.cashflowStatement
    .freeCashFlow as number;
  const netDebt = financialData.balanceSheet.netDebt as number;

  // Validate that we have the necessary data
  if (
    typeof ttmRevenue !== "number" ||
    typeof ttmFreeCashFlow !== "number" ||
    typeof netDebt !== "number"
  ) {
    logger.error("Missing required TTM financial data", {
      ttmRevenue,
      ttmFreeCashFlow,
      netDebt,
    });
    throw new Error(
      "Revenue, Free Cash Flow, or Net Debt data is missing from TTM report"
    );
  }

  logger.info("Parsed TTM metrics", {
    ttmRevenue,
    ttmFreeCashFlow,
    netDebt,
    fcfMargin: (ttmFreeCashFlow / ttmRevenue) * 100,
  });

  // Step 4: Call reverse DCF function
  try {
    const reverseDcfResults = await reverseDcf({
      currentPrice: quote.price,
      marketCap: quote.marketCap,
      sharesOutstanding: quote.sharesOutstanding,
      ttmRevenue,
      ttmFreeCashFlow,
      projectionYears: 5,
      terminalGrowthRate: 0.025,
    });

    logger.info("Reverse DCF calculation completed", {
      resultsCount: reverseDcfResults.length,
    });

    // Stream success
    await streams["stock-analysis-stream"].set("analysis", traceId, {
      id: traceId,
      symbol,
      status: "Reverse DCF analysis completed successfully.",
    });

    // Store results for downstream steps
    await state.set("reverse-dcf-analysis", traceId, {
      symbol,
      currentPrice: quote.price,
      marketCap: quote.marketCap,
      sharesOutstanding: quote.sharesOutstanding,
      ttmRevenue,
      ttmFreeCashFlow,
      netDebt,
      fcfMargin: ttmFreeCashFlow / ttmRevenue,
      impliedGrowthRates: reverseDcfResults,
      generatedAt: new Date().toISOString(),
    });

    logger.info("State saved, emitting finish event");

    await emit({
      topic: "finish-reverse-dcf-analysis",
      data: { symbol },
    });

    logger.info("Reverse DCF step completed successfully");
  } catch (error) {
    logger.error("Reverse DCF calculation failed", { error });

    await streams["stock-analysis-stream"].set("analysis", traceId, {
      id: traceId,
      symbol,
      status: `Reverse DCF failed: ${error instanceof Error ? error.message : "Unknown error"}`,
    });

    throw error;
  }
};

// Re-export from shared types package
export { reverseDcfAnalysisSchema, type ReverseDcfAnalysis } from "@repo/types";
