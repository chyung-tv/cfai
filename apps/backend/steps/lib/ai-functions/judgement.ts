import { generateObject } from "ai";
import { google } from "./ai";
import { z } from "zod";
import { qualitativeAnalysisSchema } from "../../stock-analysis/qualitative-analysis.step";
import { reverseDcfAnalysisSchema } from "../../stock-analysis/reverse-dcf.step";

// 1. Define the Output Schema
// This schema maps the AI's judgement to the specific reverse DCF scenarios
export const growthJudgementSchema = z.object({
  symbol: z.string(),

  // The AI's independent view of the world (unbiased by current price)
  independentPrediction: z.object({
    predictedCagr: z
      .number()
      .describe(
        "The most likely 5-year revenue CAGR based on qualitative analysis (e.g., 0.12 for 12%)"
      ),
    confidence: z.number().min(0).max(1),
    keyDrivers: z
      .array(z.string())
      .describe("Top 3 factors driving this specific prediction"),
  }),

  // Explicit DCF Assumptions for the model
  dcfAssumptions: z.object({
    revenueGrowthRates: z
      .array(z.number())
      .length(5)
      .describe(
        "Explicit revenue growth rates for the next 5 years (e.g. [0.15, 0.14, 0.13, 0.12, 0.10])"
      ),
    terminalGrowthRate: z
      .number()
      .describe("Long-term terminal growth rate (e.g. 0.03)"),
    discountRate: z
      .number()
      .describe(
        "Appropriate discount rate for this company's risk profile (e.g. 0.10)"
      ),
  }),

  // Evaluation of the market's implied expectations
  scenarios: z
    .array(
      z.object({
        discountRate: z.number(),
        impliedGrowth: z.number(),
        feasibility: z
          .enum(["VERY_HIGH", "HIGH", "MEDIUM", "LOW", "VERY_LOW"])
          .describe("Likelihood of achieving this specific growth rate"),
        gapAnalysis: z
          .string()
          .describe(
            "Brief explanation of the gap between predicted and implied growth"
          ),
      })
    )
    .describe(
      "Evaluation of each discount rate scenario provided in the input"
    ),

  // Overall Verdict
  verdict: z.enum(["UNDERVALUED", "FAIR_VALUE", "OVERVALUED", "UNCERTAIN"]),
  reasoning: z
    .array(z.string())
    .describe("High-level reasoning for the verdict"),
  generatedAt: z.string(),
});

export type GrowthJudgement = z.infer<typeof growthJudgementSchema>;

/**
 * AI Growth Judgement Function
 * Uses a reasoning model to compare market expectations (Reverse DCF) vs. Qualitative Reality.
 */
export async function evaluateGrowthFeasibility(
  qualitativeAnalysis: z.infer<typeof qualitativeAnalysisSchema>,
  reverseDcfAnalysis: z.infer<typeof reverseDcfAnalysisSchema>
): Promise<GrowthJudgement> {
  const { symbol, thesis, reasoning } = qualitativeAnalysis;
  const { impliedGrowthRates, currentPrice, fcfMargin } = reverseDcfAnalysis;

  // Construct the prompt context
  const promptContext = `
    STOCK: ${symbol}
    CURRENT PRICE: $${currentPrice}
    IMPLIED FCF MARGIN: ${(fcfMargin * 100).toFixed(1)}%

    QUALITATIVE THESIS:
    ${thesis}

    KEY REASONING POINTS:
    ${reasoning.join("\n")}

    MARKET EXPECTATIONS (REVERSE DCF):
    The following table shows what Revenue CAGR is required to justify the current price at different Discount Rates (Target Returns):
    ${impliedGrowthRates
      .map(
        (r) =>
          `- To get a ${(r.discountRate * 100).toFixed(1)}% return, company must grow at ${(r.impliedRevenueCAGR * 100).toFixed(1)}%`
      )
      .join("\n")}
  `;

  const result = await generateObject({
    model: google("gemini-2.5-flash"), // Using the reasoning model
    schema: growthJudgementSchema,
    prompt: `
      You are a skeptical, high-precision Equity Research Analyst.
      
      Your Goal: Determine if the growth rates implied by the current stock price are realistic given the qualitative analysis.

      Task 1: Form an INDEPENDENT view of the company's likely revenue growth (CAGR) for the next 5 years. Ignore the stock price for this. Base it purely on the thesis, industry trends, and competitive position.
      
      Task 2: Generate explicit DCF assumptions.
      - Provide 5 years of specific revenue growth rates.
      - Choose a terminal growth rate (usually 2-4%).
      - Choose a discount rate (WACC) appropriate for the risk.

      Task 3: Compare your independent view against the "Market Expectations" scenarios provided. 
      - If the Implied Growth is much LOWER than your prediction -> Feasibility is HIGH (Easy to beat).
      - If the Implied Growth is much HIGHER than your prediction -> Feasibility is LOW (Hard to achieve).
      
      Task 4: Render a verdict.
      - Undervalued: You can get a high return (e.g. >9%) with feasible growth.
      - Overvalued: Even for a low return (e.g. <7%), the required growth is unrealistic.

      Context:
      ${promptContext}
    `,
  });

  return {
    ...result.object,
    generatedAt: new Date().toISOString(),
  };
}
