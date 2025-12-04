// steps/stock-analysis/stock-analysis.stream.ts
import { z } from "zod";
import { StreamConfig } from "motia";
import { dcfResultSchema } from "./dcf.step";
import { growthJudgementSchema } from "./judgement.step";
import { ratingSchema } from "../lib/ai-functions/rating";
import { thesisSchema } from "../lib/ai-functions/parseThesis";

// Define the packed data schema
export const packedDataSchema = z.object({
  id: z.string(),
  symbol: z.string(),
  price: z.number(),
  score: z.number(),
  tier: z.string(),
  moat: z.string(),
  valuationStatus: z.string(),
  thesis: thesisSchema,
  dcf: dcfResultSchema,
  financials: z.object({
    revenue: z.number(),
    netIncome: z.number(),
    fcf: z.number(),
    netDebt: z.number(),
  }),
});

// Define the complete stream schema
export const streamSchema = z.object({
  id: z.string(), // Required by Motia for stream items
  symbol: z.string(),
  status: z.string(),
  data: packedDataSchema.optional(),
});

export const config: StreamConfig = {
  name: "stock-analysis-stream",
  schema: streamSchema,
  baseConfig: {
    storageType: "default",
  },
};

// Export inferred types for use in backend and frontend
export type StockAnalysisStreamData = z.infer<typeof streamSchema>;
export type PackedAnalysisData = z.infer<typeof packedDataSchema>;
