import { ProjectionSchema } from "../lib/ai-functions/projection-judge";
import { EventConfig, Handlers } from "motia";
import { performCustomDCF } from "../lib/functions/dcf";
import z from "zod";

const inputSchema = z.object({
  symbol: z.string(),
});

export const config: EventConfig = {
  name: "DCF",
  type: "event",
  description: "Process DCF with projecttions",
  subscribes: ["finish-projection-judge"],
  emits: ["finish-dcf"],
  flows: ["stock-analysis-flow"],
  input: inputSchema,
};

export const handler: Handlers["DCF"] = async (
  input,
  { logger, state, emit, traceId, streams }
) => {
  const { symbol } = input;
  logger.info("Starting DCF processing for", { symbol });
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Calculating DCF from the verified projections...",
  });
  // Retrieve projection judgment from state
  logger.info("Retrieving projection judgment from state", { traceId });
  const projection = await state.get("projection-judge", traceId);
  const parsedProjection = ProjectionSchema.parse(projection);

  // Prepare AI parameters for dcf function
  const aiParams = {
    revenueGrowthRates: parsedProjection.revProjections.map(
      (p) => p.growthRate
    ),
    terminalGrowthRate: parsedProjection.terminalGrowth.rate,
    discountRate: parsedProjection.discount.rate,
  };
  const dcfInput = {
    aiParams,
    symbol,
  };
  //   Perform DCF processing
  const result = await performCustomDCF(dcfInput);

  // Save DCF result to state
  logger.info("Saving DCF result to state", { traceId });
  await state.set("dcf", traceId, result);

  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "DCF calculation completed.",
  });

  await emit({
    topic: "finish-dcf",
    data: {
      symbol,
    },
  });
};

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
});

export type DCFResult = z.infer<typeof dcfResultSchema>;
