import { QualitativeAnalysis } from "../../stock-analysis/qualitative-analysis.step";
import { DCFResult } from "../functions/dcf";
import { GrowthJudgement } from "../../stock-analysis/judgement.step";
import { generateObject } from "ai";
import { z } from "zod";
import { google } from "./ai";
import { ratingSchema, type StockRating } from "@repo/types";

export { ratingSchema, type StockRating } from "@repo/types";

type RatingInput = {
  symbol: string;
  dcfData: NonNullable<DCFResult>;
  qualitativeAnalysisData: QualitativeAnalysis;
  growthJudgementData: GrowthJudgement;
};

export async function rateStock(input: RatingInput): Promise<StockRating> {
  const { symbol, dcfData, qualitativeAnalysisData, growthJudgementData } =
    input;

  console.log(`\n=== Generating comprehensive rating for ${symbol} ===`);

  // Prepare comprehensive context for the AI
  const systemPrompt = `You are a seasoned equity research analyst with expertise in fundamental analysis, competitive strategy, and portfolio management. 

Your task is to provide a comprehensive investment rating by synthesizing:
1. DCF valuation results (intrinsic value, margin analysis, projections)
2. Qualitative business analysis (competitive position, management, industry dynamics)
3. Growth Feasibility Judgement (AI's independent view vs Market expectations)

Be rigorous, objective, and conservative in your assessments. Consider both bull and bear cases.`;

  const userPrompt = `Analyze ${symbol} and provide a complete investment rating.

**DCF Valuation Results:**
- Intrinsic Value per Share: $${dcfData.intrinsicValuePerShare}
- Implied FCF Margin: ${(dcfData.impliedMargin * 100).toFixed(2)}%
- Discount Rate Used: ${(dcfData.usedDiscountRate * 100).toFixed(2)}%
- Enterprise Value: $${dcfData.enterpriseValue.toLocaleString()}
- Equity Value: $${dcfData.equityValue.toLocaleString()}

**Growth Feasibility Judgement:**
- AI Independent Prediction (5y CAGR): ${(
    growthJudgementData.independentPrediction.predictedCagr * 100
  ).toFixed(2)}%
- Confidence: ${(
    growthJudgementData.independentPrediction.confidence * 100
  ).toFixed(0)}%
- Verdict: ${growthJudgementData.verdict}
- Reasoning: ${growthJudgementData.reasoning.join("; ")}

**DCF Assumptions Used:**
- Revenue Growth (Next 5 Years): ${growthJudgementData.dcfAssumptions.revenueGrowthRates
    .map((r) => (r * 100).toFixed(1) + "%")
    .join(", ")}
- Terminal Growth: ${(
    growthJudgementData.dcfAssumptions.terminalGrowthRate * 100
  ).toFixed(2)}%
- Discount Rate: ${(
    growthJudgementData.dcfAssumptions.discountRate * 100
  ).toFixed(2)}%

**Qualitative Analysis:**
${qualitativeAnalysisData.thesis}

**Reasoning & Context:**
${qualitativeAnalysisData.reasoning}

Based on this comprehensive analysis, provide your detailed investment rating covering all aspects: business quality tier, economic moat, industry trends, market structure, portfolio function, and actionable recommendation.`;

  const result = await generateObject({
    model: google("gemini-2.5-flash"),
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
