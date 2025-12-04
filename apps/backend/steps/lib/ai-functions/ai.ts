import { createGoogleGenerativeAI } from "@ai-sdk/google";
import { config } from "dotenv";

config({ path: ".env.local" });

export const google = createGoogleGenerativeAI({
  apiKey: process.env.GOOGLE_API_KEY,
});
