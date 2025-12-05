import { generateObject } from "ai";
import { z } from "zod";
import { google } from "./ai";
import { thesisSchema, type StockQualitativeAnalysis } from "@repo/types";

export { thesisSchema, type StockQualitativeAnalysis } from "@repo/types";

export async function parseThesis(thesis: string) {
  const parsedThesis = await generateObject({
    model: google("gemini-2.5-flash"),
    schema: thesisSchema,
    temperature: 0.3,
    prompt: `You are a financial analyst. Please parse the following thesis into a JSON object: ${thesis}`,
  });

  return parsedThesis.object;
}
