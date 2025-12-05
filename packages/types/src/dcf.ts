import { z } from "zod";

/**
 * DCF (Discounted Cash Flow) Result Schema
 * Contains intrinsic valuation and sensitivity analysis
 */
export const dcfResultSchema = z.object({
  intrinsicValuePerShare: z.number(),
  impliedMargin: z.number(),
  usedDiscountRate: z.number(),
  sumPvFcf: z.number(),
  terminalValue: z.number(),
  presentTerminalValue: z.number(),
  enterpriseValue: z.number(),
  equityValue: z.number(),
  projections: z.array(
    z.object({
      year: z.number(),
      revenue: z.number(),
      fcf: z.number(),
      pvFCF: z.number(),
    })
  ),
  upsideDownside: z.number(),
  sensitivity: z.object({
    terminalGrowthRates: z.array(z.number()),
    discountRates: z.array(z.number()),
    values: z.array(z.array(z.number())),
  }),
});

export type DCFResult = z.infer<typeof dcfResultSchema>;
