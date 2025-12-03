import { QualitativeAnalysis } from "../../stock-analysis/qualitative-analysis.step";
import { DCFResult } from "../functions/dcf";
import { ProjectionResult } from "./projection-judge";
import { generateObject } from "ai";
import { z } from "zod";
import { google } from "./ai";

type RatingInput = {
  symbol: string;
  dcfData: NonNullable<DCFResult>; // Data is validated in rating.step.ts before calling this function
  qualitativeAnalysisData: QualitativeAnalysis;
  projectionJudgeData: ProjectionResult;
};

// Comprehensive Stock Rating Schema
export const ratingSchema = z.object({
  symbol: z.string().describe("Stock ticker symbol"),

  // Overall Business Quality Tier
  tier: z.object({
    classification: z
      .enum([
        "enduring_moat",
        "strong_moat",
        "good_business",
        "nothing_special",
        "junk_company",
      ])
      .describe(
        "Overall business quality: enduring_moat (exceptional), strong_moat (very good), good_business (solid), nothing_special (mediocre), junk_company (poor)"
      ),
    reason: z
      .string()
      .describe(
        "Detailed explanation for the tier classification based on competitive advantages, financial health, and long-term prospects"
      ),
  }),

  // Economic Moat Analysis
  economicMoat: z.object({
    primaryMoat: z
      .enum([
        "cost_advantage",
        "network_effect",
        "intangible_assets",
        "switching_costs",
        "efficient_scale",
        "technology_leadership",
        "brand_strength",
        "regulatory_barriers",
        "data_advantage",
        "none",
      ])
      .describe(
        "Primary competitive advantage: cost_advantage, network_effect, intangible_assets (patents/licenses), switching_costs, efficient_scale, technology_leadership, brand_strength, regulatory_barriers, data_advantage, or none"
      ),
    secondaryMoats: z
      .array(
        z.enum([
          "cost_advantage",
          "network_effect",
          "intangible_assets",
          "switching_costs",
          "efficient_scale",
          "technology_leadership",
          "brand_strength",
          "regulatory_barriers",
          "data_advantage",
        ])
      )
      .optional()
      .describe("Additional competitive advantages if applicable"),
    reason: z
      .string()
      .describe(
        "Explanation of how the moat(s) protect the business from competition and enable sustained profitability"
      ),
  }),

  // Industry Trend
  industryTrend: z.object({
    trend: z
      .enum([
        "booming",
        "growing",
        "cyclic_upswing",
        "cyclic_downswing",
        "stagnant",
        "headwind",
        "declining",
      ])
      .describe(
        "Current industry trajectory: booming (explosive growth), growing (steady expansion), cyclic_upswing/cyclic_downswing (cyclical), stagnant (flat), headwind (facing challenges), declining (shrinking)"
      ),
    reason: z
      .string()
      .describe(
        "Analysis of industry dynamics, growth drivers, secular trends, and macroeconomic factors affecting the sector"
      ),
  }),

  // Market Structure
  marketStructure: z.object({
    structure: z
      .enum([
        "global_monopoly",
        "segment_monopoly",
        "local_monopoly",
        "major_oligopoly_player",
        "minor_oligopoly_player",
        "consolidating_monopoly",
        "monopolistic_competition",
        "perfect_competition",
        "emerging_duopoly",
      ])
      .describe(
        "Competitive landscape: global/segment/local monopoly, major/minor oligopoly player, consolidating monopoly, monopolistic competition, perfect competition, emerging duopoly"
      ),
    marketShare: z
      .number()
      .optional()
      .describe("Estimated market share percentage if available"),
    reason: z
      .string()
      .describe(
        "Assessment of competitive intensity, market concentration, barriers to entry, and company's competitive position"
      ),
  }),

  // Portfolio Use/Function
  portfolioFunction: z.object({
    primaryFunction: z
      .enum([
        "capital_appreciation",
        "stability",
        "stable_cashflow",
        "volatile_cashflow",
        "growth_and_income",
        "speculation",
        "hedge",
        "diversification",
      ])
      .describe(
        "Primary portfolio role: capital_appreciation (growth), stability (defensive), stable_cashflow (dividend income), volatile_cashflow (cyclical income), growth_and_income (balanced), speculation (high risk), hedge (protection), diversification (portfolio balance)"
      ),
    riskProfile: z
      .enum(["very_low", "low", "moderate", "high", "very_high"])
      .describe("Risk level of the investment"),
    reason: z
      .string()
      .describe(
        "Explanation of how this stock fits into a portfolio strategy, expected return profile, and risk characteristics"
      ),
  }),

  // Investment Action
  action: z.object({
    recommendation: z
      .enum([
        "strong_buy",
        "buy",
        "accumulate",
        "hold",
        "reduce",
        "sell",
        "strong_sell",
        "avoid",
      ])
      .describe(
        "Investment recommendation: strong_buy (highly attractive), buy (attractive), accumulate (build position gradually), hold (maintain), reduce (trim position), sell (exit), strong_sell (exit urgently), avoid (don't invest)"
      ),
    targetAllocation: z
      .number()
      .min(0)
      .max(100)
      .optional()
      .describe("Suggested portfolio allocation percentage (0-100)"),
    reason: z
      .string()
      .describe(
        "Comprehensive rationale combining valuation (DCF vs current price), business quality, industry outlook, and risk-reward assessment"
      ),
  }),
});

export type StockRating = z.infer<typeof ratingSchema>;

export async function rateStock(input: RatingInput): Promise<StockRating> {
  const { symbol, dcfData, qualitativeAnalysisData, projectionJudgeData } =
    input;

  console.log(`\n=== Generating comprehensive rating for ${symbol} ===`);

  // Prepare comprehensive context for the AI
  const systemPrompt = `You are a seasoned equity research analyst with expertise in fundamental analysis, competitive strategy, and portfolio management. 

Your task is to provide a comprehensive investment rating by synthesizing:
1. DCF valuation results (intrinsic value, margin analysis, projections)
2. Qualitative business analysis (competitive position, management, industry dynamics)
3. Projection quality assessment (growth assumptions, margin sustainability)

Be rigorous, objective, and conservative in your assessments. Consider both bull and bear cases.`;

  const userPrompt = `Analyze ${symbol} and provide a complete investment rating.

**DCF Valuation Results:**
- Intrinsic Value per Share: $${dcfData.intrinsicValuePerShare}
- Implied FCF Margin: ${(dcfData.impliedMargin * 100).toFixed(2)}%
- Discount Rate Used: ${(dcfData.usedDiscountRate * 100).toFixed(2)}%
- Enterprise Value: $${dcfData.enterpriseValue.toLocaleString()}
- Equity Value: $${dcfData.equityValue.toLocaleString()}

**Projection Quality:**
- Audit Status: ${
    projectionJudgeData.audit.isLegitimate ? "LEGITIMATE" : "QUESTIONABLE"
  }
- Optimism Check: ${projectionJudgeData.audit.optimismCheck}
- Consistency Check: ${projectionJudgeData.audit.consistencyCheck}
${
  projectionJudgeData.audit.correctionNeeded
    ? `- Concerns: ${projectionJudgeData.audit.correctionNeeded}`
    : ""
}
- Terminal Growth Rate: ${(
    projectionJudgeData.terminalGrowth.rate * 100
  ).toFixed(2)}% (${projectionJudgeData.terminalGrowth.keyAssumption})
- Discount Rate: ${(projectionJudgeData.discount.rate * 100).toFixed(2)}% (${
    projectionJudgeData.discount.keyAssumption
  })

**10-Year Revenue Projections:**
${projectionJudgeData.revProjections
  .map(
    (p) =>
      `Year ${p.year}: $${p.revenue.toLocaleString()} (${(
        p.growthRate * 100
      ).toFixed(1)}% growth, ${(p.operatingMargin * 100).toFixed(
        1
      )}% margin) - ${p.keyAssumption}`
  )
  .join("\n")}

**Qualitative Analysis:**
${qualitativeAnalysisData.thesis}

**Reasoning & Context:**
${qualitativeAnalysisData.reasoning}

Based on this comprehensive analysis, provide your detailed investment rating covering all aspects: business quality tier, economic moat, industry trends, market structure, portfolio function, and actionable recommendation.`;

  const result = await generateObject({
    model: google("gemini-2.5-pro"),
    schema: ratingSchema,
    messages: [
      {
        role: "system",
        content: systemPrompt,
      },
      {
        role: "user",
        content: userPrompt,
      },
    ],
    temperature: 0.3, // Lower temperature for more consistent, analytical output
  });

  console.log(`✅ Rating generated for ${symbol}`);
  console.log(`   Tier: ${result.object.tier.classification}`);
  console.log(`   Action: ${result.object.action.recommendation}`);

  return result.object;
}

export type RatingResult = z.infer<typeof ratingSchema>;
