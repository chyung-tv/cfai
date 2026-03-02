from __future__ import annotations

from datetime import date


def build_deep_research_prompt(
    *,
    symbol: str,
    company_name: str | None = None,
    as_of_date: date | None = None,
) -> str:
    normalized_symbol = symbol.strip().upper()
    normalized_company = company_name.strip() if company_name else "Unknown"
    report_date = (as_of_date or date.today()).isoformat()

    return f"""
Act as a seasoned, critical CFA charterholder and expert business analyst.
Conduct a professional, CFA-standard analysis for the requested company using real and up-to-date financial data.
When sources conflict, prioritize SEC filings, then investor relations disclosures, then trusted financial media.

Target company:
- Symbol: {normalized_symbol}
- Company name (if available): {normalized_company}
- Analysis as-of date: {report_date}

Purpose:
1) Deliver comprehensive and in-depth financial/business analysis at CFA-level rigor.
2) Provide actionable insights and a concise investment verdict supported by explicit assumptions.
3) Keep all major claims source-cited.

Strict output requirements:
- Write the final report in markdown.
- Start with title block and metadata (date, analyst classification, subject, ticker, sector if known, recommendation).
- Follow this section order exactly:
  1. Executive Summary (max 5 sentences)
  2. Company Profile (Business Essence & Model)
     - Value proposition, revenue streams, cost structure, customer segments, channels,
       key activities/resources, competitive advantage, economic moat
     - Business segments, Porter's Five Forces, internal/external growth and decline drivers,
       customer choice rationale vs peers, brand/social sentiment
  3. Management Profile
     - Key executives, tenure impact, compensation structure and incentives
  4. Industry Profile
     - 10-year industry outlook, market structure, competitive landscape, ecosystem,
       suppliers/regulation/disruption risks, secular drivers
  5. Financial Profile
     - Trailing 5-year ROE, ROIC, ROCE (with peer comparison)
     - 10-year revenue CAGR and operating margin projection
     - Include a clear assumptions table explaining the model basis
  6. Recent Developments (last 6 months)
     - Notable company/sector events and >10% stock moves with likely drivers
  7. Life Line
     - Condense the entire research into the single most critical business lifeline
     - Explicitly name one factor the company thrives on
     - Explicitly describe the break condition: if this factor fails, why the company is in danger
  8. Gemini Verdict
     - Clear investment decision with viewpoint-based conditions
     - Example style: attractive for growth-focused investors, less suitable for cash-flow-focused investors
     - Include alternatives in related industry/assets

Methodology and transparency requirements:
- Explicitly explain reasoning for complex judgments and projections.
- Mark unknown data as unavailable rather than fabricating.
- For each major quantitative statement, include source attribution inline and also in Works Cited.
- Include a final "Works Cited" section with URL links.

Quality bar:
- Professional, objective, and analytical tone.
- Use precise financial terminology while remaining understandable.
- Prefer primary sources (SEC 10-K/10-Q/8-K, earnings call transcripts, investor presentations).
- Keep conclusions objective and evidence-driven; do not personalize conclusions by user risk profile input.
""".strip()
