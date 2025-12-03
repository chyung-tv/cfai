// steps/stock-analysis/stock-analysis.stream.ts
import { z } from "zod";
import { StreamConfig } from "motia";
import { dcfResultSchema } from "./dcf.step";
import { ProjectionSchema } from "../lib/ai-functions/projection-judge";
import { ratingSchema } from "../lib/ai-functions/rating";
import { thesisSchema } from "../lib/ai-functions/parseThesis";

// Define the packed data schema
export const packedDataSchema = z.object({
  symbol: z.string(),
  dcfData: dcfResultSchema,
  structuredThesis: thesisSchema, // Now fully typed!
  projectionJudgeData: ProjectionSchema,
  ratingData: ratingSchema,
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
