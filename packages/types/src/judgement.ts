import { z } from "zod";

/**
 * Growth Judgement Schema
 * AI's independent growth prediction vs market implied growth
 */
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
