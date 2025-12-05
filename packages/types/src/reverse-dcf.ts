import { z } from "zod";

/**
 * Reverse DCF Result Schema
 * Individual scenario mapping discount rate to implied growth
 */
export const reverseDcfResultSchema = z.object({
  discountRate: z.number(),
  impliedRevenueCAGR: z.number(),
});

export type ReverseDcfResult = z.infer<typeof reverseDcfResultSchema>;

/**
 * Complete Reverse DCF Analysis Schema
 * Contains market data and implied growth scenarios
 */
export const reverseDcfAnalysisSchema = z.object({
  symbol: z.string(),
  currentPrice: z.number(),
  marketCap: z.number(),
  sharesOutstanding: z.number(),
  ttmRevenue: z.number(),
  ttmFreeCashFlow: z.number(),
  netDebt: z.number(),
  fcfMargin: z.number(),
  impliedGrowthRates: z.array(reverseDcfResultSchema),
  generatedAt: z.string(),
});

export type ReverseDcfAnalysis = z.infer<typeof reverseDcfAnalysisSchema>;
