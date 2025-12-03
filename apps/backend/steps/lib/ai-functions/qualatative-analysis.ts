import { perplexity } from "./ai";
import { generateText } from "ai";

export async function qualitativeStockAnalysis(symbol: string) {
  const { reasoning, text } = await generateText({
    model: perplexity("sonar"),
    system: `You are a senior equity research analyst conducting comprehensive fundamental analysis for institutional investors. Your analysis will inform investment decisions and financial modeling, so prioritize:

1. DEPTH over brevity - provide extensive analysis with supporting evidence
2. ACCURACY - cite authoritative sources (SEC filings, earnings transcripts, industry reports)
3. OBJECTIVITY - present both bull and bear cases with balanced assessment
4. ACTIONABLE INSIGHTS - focus on material drivers that impact valuation

For every significant claim, include inline citations [URL]. When data is unavailable or uncertain, explicitly state limitations rather than speculating.`,

    prompt: `Conduct a comprehensive qualitative investment analysis for ${symbol}. Structure your analysis as a detailed investment memo covering:

## EXECUTIVE SUMMARY
- Investment thesis in 3-5 sentences
- Key strengths and risks
- Industry positioning summary

## BUSINESS PROFILE
- Core business model, revenue streams, and value proposition
- **Economic Moat Analysis**: Evaluate competitive advantages (brand, network effects, cost advantages, switching costs, regulatory barriers)
- **Porter's Five Forces**: Analyze competitive intensity, supplier/buyer power, substitutes, barriers to entry
- **Key Growth Drivers**: Internal initiatives and external catalysts (quantify where possible)
- **Strategic Risks**: Threats to business model, competitive vulnerabilities, execution risks

## INDUSTRY DYNAMICS
- Industry structure and total addressable market (TAM)
- **10-Year Growth Outlook**: Industry CAGR projections with supporting rationale (cite analyst reports, market research)
- **Secular Trends**: Technology shifts, regulatory changes, consumer behavior evolution
- **Competitive Landscape**: Market share analysis, key competitors, differentiation factors

## MANAGEMENT & GOVERNANCE
- Leadership team background, track record, tenure
- **Capital Allocation**: History of M&A, buybacks, dividends, R&D investment
- **Compensation Alignment**: Analyze executive comp structure vs. shareholder value creation
- **Corporate Governance**: Board independence, shareholder rights, related-party issues

## FINANCIAL QUALITY ASSESSMENT
- Revenue quality and sustainability (recurring vs. one-time, customer concentration)
- ROIC, ROCE metrics and peer comparison
- Historical margin trends and operating leverage
- Cash flow generation and working capital efficiency
- Balance sheet strength (debt levels, covenant headroom, liquidity)

## RECENT DEVELOPMENTS (6 months from ${new Date().toISOString()})
- Material news, acquisitions, product launches
- Earnings surprises and guidance changes  
- Stock price movements and analyst revisions
- Regulatory or legal developments

## CRITICAL ASSUMPTIONS FOR MODELING
- Industry growth rates to baseline revenue projections
- Margin expansion/contraction drivers
- Reinvestment needs (capex, working capital)
- Terminal value considerations (mature growth rate, competitive position sustainability)

Provide specific numbers, timeframes, and sources. Aim for 1500-2500 words of substantive analysis.`,
    providerOptions: {
      perplexity: {
        temperature: 0.3,
      },
    },
  });
  return { reasoning, text };
}
