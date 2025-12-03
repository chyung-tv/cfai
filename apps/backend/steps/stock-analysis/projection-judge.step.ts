import { generateVerifiedProjections } from "../lib/ai-functions/projection-judge";

import { EventConfig, Handlers } from "motia";
import z from "zod";

const inputSchema = z.object({
  symbol: z.string(),
});

export const config: EventConfig = {
  name: "ProjectionJudge",
  type: "event",
  description: "Construct and judge projections for DCF",
  subscribes: ["finish-stock-qualitative-analysis"],
  emits: ["finish-projection-judge"],
  flows: ["stock-analysis-flow"],
  input: inputSchema,
};

export const handler: Handlers["ProjectionJudge"] = async (
  input,
  { logger, state, emit, traceId, streams }
) => {
  const { symbol } = input;
  logger.info("Starting projection judgment", { symbol });

  // Retrieve qualitative analysis from state
  logger.info("Retrieving qualitative analysis from state", { traceId });
  const data = await state.get("stock-qualitative-analysis", traceId);
  logger.info("Validating qualitative analysis", { traceId });
  const validatedData = z.safeParse(
    z.object({
      thesis: z.string(),
      reasoning: z.string(),
      symbol: z.string(),
      generatedAt: z.string(),
    }),
    data
  );

  //   Perform projection judgment logic here
  logger.info("Generating verified projections", { traceId });
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Gemini is generating verified projections...",
  });

  const projectionJudgment = await generateVerifiedProjections(
    input.symbol,
    validatedData.data?.thesis || "",
    3,
    true
  );

  logger.info("Storing projection judgment in state", { traceId });
  await state.set("projection-judge", traceId, projectionJudgment);

  await streams["stock-analysis-stream"].set("analysis", traceId, {
    id: traceId,
    symbol,
    status: "Gemini has generated verified projections.",
  });

  logger.info("Emitting finish event for projection judgment", { traceId });
  await emit({
    topic: "finish-projection-judge",
    data: {
      symbol: input.symbol,
    },
  });
  logger.info("Projection judgment process complete", { traceId });
};
