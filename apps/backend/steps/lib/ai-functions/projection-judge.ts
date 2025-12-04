import { generateObject } from "ai";
import { google } from "./ai";
import { z } from "zod";

// 1. Define the Schema
// This forces the model to "show its work" before giving the final array.
export const ProjectionSchema = z.object({
  // The "Chain of Thought" - Research Grounding
  marketContext: z
    .string()
    .describe(
      "Summary of industry CAGR and specific company drivers used for this calculation."
    ),

  // The Data
  revProjections: z
    .array(
      z.object({
        year: z.number(),
        revenue: z.number(),
        growthRate: z
          .number()
          .describe("Percentage revenue growth, e.g., 0.15 for 15%"),
        operatingMargin: z.number(),
        keyAssumption: z
          .string()
          .describe("Why this specific number? e.g. 'New factory opens'"),
      })
    )
    .length(10)
    .describe("10-year projection array"),
  terminalGrowth: z.object({
    rate: z
      .number()
      .describe("Terminal Growth Rate as decimal, e.g. 0.03 for 3%"),
    keyAssumption: z
      .string()
      .describe("Rationale for chosen terminal growth rate"),
  }),
  discount: z.object({
    rate: z
      .number()
      .max(1)
      .describe("Discount Rate as decimal, e.g. 0.08 for 8%"),
    keyAssumption: z.string().describe("Rationale for chosen discount rate"),
  }),

  // The Self-Judgment (The "Agent" part)
  audit: z.object({
    optimismCheck: z
      .string()
      .describe(
        "Critique: Are these numbers too optimistic compared to historical averages?"
      ),
    consistencyCheck: z
      .string()
      .describe(
        "Critique: Do margins align with the cost structure analysis? Do terminal values make sense? Is discount rate appropriate?"
      ),
    isLegitimate: z
      .boolean()
      .describe(
        "Final Verdict: Set to TRUE only if projections are realistic and grounded. Set FALSE if they need correction."
      ),
    correctionNeeded: z
      .string()
      .optional()
      .describe("If isLegitimate is false, explain what needs to be fixed."),
  }),
});

export type ProjectionResult = z.infer<typeof ProjectionSchema>;

// 2. The Self-Correcting Function
export async function generateVerifiedProjections(
  ticker: string,
  baseAnalysis: string,
  maxRetries = 3,
  returnOnFailure = true // New flag: accept result even if audit fails
): Promise<ProjectionResult> {
  const messages: any[] = [
    {
      role: "system",
      content: `You are a strict Financial Modeler. 
      1. Analyze the provided company report.
      2. Generate a 10-year revenue and margin projection.
      3. CRITICALLY AUDIT your own numbers. 
      4. If the growth rate exceeds historical averages without a catalyst, mark 'isLegitimate' as FALSE.
      5. If margins expand indefinitely without scale economies, mark 'isLegitimate' as FALSE.`,
    },
    {
      role: "user",
      content: `Create projections for ${ticker} based on this analysis: ${JSON.stringify(
        baseAnalysis
      )}`,
    },
  ];

  let attempt = 0;
  let lastResult: ProjectionResult | null = null;

  while (attempt < maxRetries) {
    console.log(`Attempt ${attempt + 1} for ${ticker}...`);

    const result = await generateObject({
      model: google("gemini-2.5-flash"),
      schema: ProjectionSchema,
      messages: messages,
      temperature: 0.3 + attempt * 0.1,
    });

    const output = result.object;
    lastResult = output; // Store each attempt

    // Check the model's own verdict
    if (output.audit.isLegitimate) {
      console.log("✅ Projections passed internal audit.");
      return output;
    }

    // If we are here, audit failed
    console.warn(
      `⚠️ Audit failed: ${output.audit.correctionNeeded}. Retrying...`
    );

    // If this is the last attempt AND returnOnFailure is true, return anyway
    if (attempt === maxRetries - 1 && returnOnFailure && lastResult) {
      console.warn(
        `Max retries reached. Returning last result despite audit failure for ${ticker}`
      );
      return lastResult;
    }

    // Otherwise, feed back for retry
    messages.push({
      role: "assistant",
      content: JSON.stringify(output),
    });

    messages.push({
      role: "user",
      content: `Your previous projection was rejected by your own audit. 
      Reason: ${output.audit.correctionNeeded}. 
      Please regenerate the projections fixing these errors. 
      Ensure 'isLegitimate' is true this time.`,
    });

    attempt++;
  }

  // If returnOnFailure is false, throw error
  throw new Error(
    `Failed to generate legitimate projections for ${ticker} after ${maxRetries} attempts.`
  );
}
