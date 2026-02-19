import { z } from "zod";
import { getCachedQuote, setCachedQuote } from "../../../lib/fmp-cache";

export const quoteSchema = z.object({
  symbol: z.string(),
  price: z.number(),
  marketCap: z.number(),
  sharesOutstanding: z.number(),
});

export type QuoteData = z.infer<typeof quoteSchema>;

export async function fetchQuote(symbol: string) {
  const cached = await getCachedQuote(symbol);
  if (cached) {
    return quoteSchema.parse(cached);
  }

  const fmpApiKey = process.env.FMP_API_KEY;
  let baseURL = process.env.FMP_BASE_URL;

  if (!fmpApiKey || !baseURL) {
    throw new Error("FMP_API_KEY or FMP_BASE_URL not set in environment");
  }

  if (baseURL && !baseURL.endsWith("/")) {
    baseURL = `${baseURL}/`;
  }

  const quoteUrl = `${baseURL}quote?symbol=${symbol}&apikey=${fmpApiKey}`;

  try {
    const quoteResponse = await fetch(quoteUrl);
    if (!quoteResponse.ok) {
      throw new Error(
        `Failed to fetch quote data: ${quoteResponse.statusText}`
      );
    }

    const quoteData = await quoteResponse.json();
    if (!Array.isArray(quoteData) || quoteData.length === 0) {
      throw new Error(`No quote data found for symbol: ${symbol}`);
    }

    const data = quoteData[0];
    if (!data.sharesOutstanding && data.marketCap && data.price) {
      data.sharesOutstanding = Math.round(data.marketCap / data.price);
    }

    const parsed = quoteSchema.parse(data);
    await setCachedQuote(symbol, parsed);
    return parsed;
  } catch (error) {
    console.error(`Error fetching quote for ${symbol}:`, error);
    throw error;
  }
}
