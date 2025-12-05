import { z } from "zod";
import { dcfResultSchema } from "./dcf";
import { thesisSchema } from "./thesis";
import { growthJudgementSchema } from "./judgement";
import { ratingSchema } from "./rating";

/**
 * Packed Analysis Data Schema
 * Complete analysis result as saved to the database
 */
export const packedDataSchema = z.object({
  id: z.string(),
  symbol: z.string(),
  price: z.number(),
  score: z.number(),
  tier: z.string(),
  moat: z.string(),
  valuationStatus: z.string(),
  thesis: thesisSchema,
  dcf: dcfResultSchema.extend({
    // Extended with growth judgement data
    scenarios: growthJudgementSchema.shape.scenarios.optional(),
    independentPrediction: growthJudgementSchema.shape.independentPrediction.optional(),
  }),
  financials: z.object({
    revenue: z.number(),
    netIncome: z.number(),
    fcf: z.number(),
    netDebt: z.number(),
  }),
  rating: ratingSchema.optional(),
});

export type PackedAnalysisData = z.infer<typeof packedDataSchema>;

/**
 * Stream Data Schema
 * Real-time status updates during analysis
 */
export const streamSchema = z.object({
  id: z.string(),
  symbol: z.string(),
  status: z.string(),
  data: packedDataSchema.optional(),
});

export type StockAnalysisStreamData = z.infer<typeof streamSchema>;
