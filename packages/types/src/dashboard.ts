import { z } from "zod";
import type { PackedAnalysisData } from "./index";

/**
 * Analysis status union type
 */
export type AnalysisStatus = "completed" | "processing" | "failed";

/**
 * User query with optional analysis result
 * Matches the Prisma UserQuery model with joined AnalysisResult
 */
export interface UserQueryWithResult {
  id: string;
  symbol: string;
  status: string;
  traceId: string | null;
  createdAt: Date;
  analysisResult: {
    id: string;
    price: number;
    dcf: PackedAnalysisData["dcf"];
  } | null;
}

/**
 * Zod schema for validating user query IDs (UUID format)
 */
export const queryIdSchema = z.string().uuid({
  message: "Invalid query ID format",
});
