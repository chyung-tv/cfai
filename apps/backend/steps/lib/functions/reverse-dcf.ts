import { z } from "zod";

/**
 * Reverse DCF Calculation
 *
 * Given current market price and fundamentals, calculates the implied revenue CAGR
 * that would justify the current valuation across different discount rates.
 *
 * Uses perpetuity model for terminal value calculation.
 */

// Input schema
export const reverseDcfInputSchema = z.object({
  // Quote data
  currentPrice: z.number().positive(),
  marketCap: z.number().positive(),
  sharesOutstanding: z.number().positive(),

  // TTM financials (company-wide, not per-share)
  ttmRevenue: z.number().positive(),
  ttmFreeCashFlow: z.number(),

  // Projection settings
  projectionYears: z.number().int().positive().default(5),
  terminalGrowthRate: z.number().default(0.025), // 2.5% perpetual growth
});

export type ReverseDcfInput = z.infer<typeof reverseDcfInputSchema>;

// Output schema
export const reverseDcfResultSchema = z.object({
  impliedRevenueCAGR: z.number(),
  discountRate: z.number(),
});

export type ReverseDcfResult = z.infer<typeof reverseDcfResultSchema>;

/**
 * Calculate intrinsic value using DCF model given a revenue CAGR
 */
function calculateDcfValue(
  ttmRevenue: number,
  fcfMargin: number,
  revenueCAGR: number,
  discountRate: number,
  projectionYears: number,
  terminalGrowthRate: number
): number {
  let presentValue = 0;
  let currentRevenue = ttmRevenue;

  // Calculate present value of projected FCF
  for (let year = 1; year <= projectionYears; year++) {
    currentRevenue = currentRevenue * (1 + revenueCAGR);
    const fcf = currentRevenue * fcfMargin;
    const discountFactor = Math.pow(1 + discountRate, year);
    presentValue += fcf / discountFactor;
  }

  // Calculate terminal value using perpetuity model
  const terminalRevenue = currentRevenue * (1 + terminalGrowthRate);
  const terminalFcf = terminalRevenue * fcfMargin;
  const terminalValue = terminalFcf / (discountRate - terminalGrowthRate);
  const discountedTerminalValue =
    terminalValue / Math.pow(1 + discountRate, projectionYears);

  return presentValue + discountedTerminalValue;
}

/**
 * Binary search to find the revenue CAGR that produces a DCF value equal to target market cap
 */
function findImpliedCAGR(
  ttmRevenue: number,
  fcfMargin: number,
  targetMarketCap: number,
  discountRate: number,
  projectionYears: number,
  terminalGrowthRate: number,
  tolerance: number = 0.0001, // 0.01% precision
  maxIterations: number = 100
): number | null {
  let low = -0.5; // -50% CAGR (extreme decline)
  let high = 1.0; // 100% CAGR (extreme growth)

  // Check if solution exists within bounds
  const lowValue = calculateDcfValue(
    ttmRevenue,
    fcfMargin,
    low,
    discountRate,
    projectionYears,
    terminalGrowthRate
  );
  const highValue = calculateDcfValue(
    ttmRevenue,
    fcfMargin,
    high,
    discountRate,
    projectionYears,
    terminalGrowthRate
  );

  if (targetMarketCap < lowValue || targetMarketCap > highValue) {
    // Target is outside reasonable bounds
    return null;
  }

  // Binary search
  for (let i = 0; i < maxIterations; i++) {
    const mid = (low + high) / 2;
    const midValue = calculateDcfValue(
      ttmRevenue,
      fcfMargin,
      mid,
      discountRate,
      projectionYears,
      terminalGrowthRate
    );

    const error = Math.abs(midValue - targetMarketCap) / targetMarketCap;
    if (error < tolerance) {
      return mid;
    }

    if (midValue < targetMarketCap) {
      low = mid;
    } else {
      high = mid;
    }
  }

  // Return best estimate if convergence not achieved
  return (low + high) / 2;
}

/**
 * Calculate implied revenue CAGR across multiple discount rates
 */
export async function reverseDcf(
  input: ReverseDcfInput
): Promise<ReverseDcfResult[]> {
  const validated = reverseDcfInputSchema.parse(input);

  const {
    currentPrice,
    marketCap,
    sharesOutstanding,
    ttmRevenue,
    ttmFreeCashFlow,
    projectionYears,
    terminalGrowthRate,
  } = validated;

  // Calculate FCF margin from TTM data
  const fcfMargin = ttmFreeCashFlow / ttmRevenue;

  // Handle edge case: negative FCF margin
  if (fcfMargin <= 0) {
    throw new Error(
      `Cannot calculate reverse DCF with negative FCF margin (${(fcfMargin * 100).toFixed(2)}%). ` +
        `Company must have positive free cash flow.`
    );
  }

  // Discount rates from 6% to 10% in 1% increments
  const discountRates = [0.06, 0.07, 0.08, 0.09, 0.1];

  const results: ReverseDcfResult[] = [];

  for (const discountRate of discountRates) {
    // Check if discount rate is valid (must be > terminal growth rate)
    if (discountRate <= terminalGrowthRate) {
      throw new Error(
        `Discount rate (${(discountRate * 100).toFixed(0)}%) must be greater than ` +
          `terminal growth rate (${(terminalGrowthRate * 100).toFixed(1)}%)`
      );
    }

    const impliedCAGR = findImpliedCAGR(
      ttmRevenue,
      fcfMargin,
      marketCap,
      discountRate,
      projectionYears,
      terminalGrowthRate
    );

    if (impliedCAGR !== null) {
      results.push({
        impliedRevenueCAGR: impliedCAGR,
        discountRate: discountRate,
      });
    }
  }

  if (results.length === 0) {
    throw new Error(
      `Could not find valid implied CAGR for any discount rate. ` +
        `Market cap may be outside reasonable valuation bounds.`
    );
  }

  return results;
}
