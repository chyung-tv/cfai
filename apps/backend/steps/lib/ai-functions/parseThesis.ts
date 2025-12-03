import { generateObject } from "ai";
import { z } from "zod";
import { google } from "./ai";

export const thesisSchema = z.object({
  executiveSummary: z
    .string()
    .describe("A concise CFA-style summary of the investment thesis."),
  businessProfile: z.object({
    essence: z
      .string()
      .describe(
        "Core business model, value prop, revenue streams, and why customers choose it."
      ),
    moat: z
      .string()
      .describe(
        "Durability and sources of competitive advantage and economic moat."
      ),
    porter: z
      .string()
      .describe("Porter's 5 forces and competitive advantage details."),
    drivers: z
      .string()
      .describe("External and internal drivers for growth or decline"),
  }),
  managementProfile: z.object({
    leadership: z.string().describe("Key managers, tenure, and impact."),
    compensationAlignment: z
      .string()
      .describe("Assessment of compensation vs shareholder value."),
  }),
  industryProfile: z.object({
    growthProjections: z.number().describe("10-year industry CAGR projection."),
    trends: z.string().describe("Major trends shaping the industry."),
    competition: z.string().describe("Market share and competitive landscape."),
  }),
  recentDevelopments: z
    .string()
    .describe("Significant news or stock movements in the last 6 months."),
});

export type StockQualitativeAnalysis = z.infer<typeof thesisSchema>;

export async function parseThesis(thesis: string) {
  const parsedThesis = await generateObject({
    model: google("gemini-2.5-flash"),
    schema: thesisSchema,
    temperature: 0.3,
    prompt: `You are a financial analyst. Please parse the following thesis into a JSON object: ${thesis}`,
  });

  return parsedThesis.object;
}
