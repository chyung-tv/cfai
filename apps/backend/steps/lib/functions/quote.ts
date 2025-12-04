import { z } from "zod";

export const quoteSchema = z.object({
  symbol: z.string(),
  price: z.number(),
  marketCap: z.number(),
  sharesOutstanding: z.number(),
});

export type QuoteData = z.infer<typeof quoteSchema>;

export async function fetchQuote(symbol: string) {
  const fmpApiKey = process.env.FMP_API_KEY;
  let baseURL = process.env.FMP_BASE_URL;

  if (!fmpApiKey || !baseURL) {
    throw new Error("FMP_API_KEY or FMP_BASE_URL not set in environment");
  }

  if (baseURL && !baseURL.endsWith("/")) {
    baseURL = `${baseURL}/`;
  }

  // Using the query parameter format as seen in other files
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

    // Calculate sharesOutstanding if missing
    if (!data.sharesOutstanding && data.marketCap && data.price) {
      data.sharesOutstanding = Math.round(data.marketCap / data.price);
    }

    return quoteSchema.parse(data);
  } catch (error) {
    console.error(`Error fetching quote for ${symbol}:`, error);
    throw error;
  }
}
