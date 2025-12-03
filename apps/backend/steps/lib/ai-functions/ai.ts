import { createGoogleGenerativeAI } from "@ai-sdk/google";
import { createPerplexity } from "@ai-sdk/perplexity";
import { config } from "dotenv";
config({ path: ".env.local" });

export const perplexity = createPerplexity({
  apiKey: process.env.PERPLEXITY_API_KEY,
});

export const google = createGoogleGenerativeAI({
  apiKey: process.env.GOOGLE_API_KEY,
});
