// steps/stock-analysis/stock-analysis.stream.ts
import { StreamConfig } from "motia";
import { z } from "zod";

// Schema for stream status updates
const streamSchema = z.object({
  id: z.string(),
  symbol: z.string(),
  status: z.string(),
});

export const config: StreamConfig = {
  name: "stock-analysis-stream",
  schema: streamSchema,
  baseConfig: {
    storageType: "default",
  },
};

// Re-export types for convenience
export type { StockAnalysisStreamData, PackedAnalysisData } from "@repo/types";
