from __future__ import annotations

import json


def build_audit_growth_likelihood_prompt(
    *,
    symbol: str,
    projection_years: int,
    optimistic_cagr_pct: float,
    median_cagr_pct: float,
    conservative_cagr_pct: float,
    report_markdown: str,
) -> str:
    case_inputs = [
        {"caseName": "optimistic", "requiredRevenueCagrPct": optimistic_cagr_pct},
        {"caseName": "median", "requiredRevenueCagrPct": median_cagr_pct},
        {"caseName": "conservative", "requiredRevenueCagrPct": conservative_cagr_pct},
    ]
    cases_json = json.dumps(case_inputs, ensure_ascii=True)

    return f"""
You are an equity-analysis audit engine.

Task:
- Evaluate whether each required revenue CAGR is achievable over a {projection_years}-year horizon.
- Base your reasoning strictly on the report content provided.
- Return ONLY one JSON object. No markdown. No extra text.

Entity:
- Symbol: {symbol}
- Projection horizon years: {projection_years}

Cases to evaluate:
{cases_json}

Required output schema:
{{
  "projectionYears": {projection_years},
  "overallAssessment": "string",
  "cases": [
    {{
      "caseName": "optimistic|median|conservative",
      "requiredRevenueCagrPct": number,
      "probabilityPct": number,
      "likelihoodLabel": "likely|possible|unlikely",
      "rationale": "string",
      "claimRefs": ["sec:SectionName", "sec:AnotherSection:Subsection"],
      "risksToThesis": ["string"],
      "supportingDrivers": ["string"]
    }}
  ],
  "quality": {{
    "parserVersion": "v1-audit-growth-likelihood",
    "missingFields": ["string"],
    "warnings": ["string"]
  }}
}}

Rules:
- Include exactly 3 case objects: optimistic, median, conservative (once each).
- Keep requiredRevenueCagrPct aligned with input values.
- probabilityPct must be between 0 and 100.
- claimRefs is REQUIRED and must be non-empty per case.
- claimRefs must use stable section-reference format that starts with "sec:" and cites relevant report sections/subsections.
- Do not fabricate facts beyond report content.
- quality.parserVersion must be "v1-audit-growth-likelihood".
- Rationale must be concrete and critical, not generic.
- For each case rationale, explicitly include:
  1) what must happen operationally (customer expansion, product ramp, capacity, software adoption, pricing/margin),
  2) what could break the case (specific bottleneck or risk trigger),
  3) why this maps to the required CAGR over {projection_years} years.
- Use at least one concrete anchor from the report per case (numeric or named event/segment when available).
- Avoid vague phrases like "strong execution" or "near-flawless execution" without concrete conditions.
- Include at least 2 `supportingDrivers` and 2 `risksToThesis` items per case.

Report markdown:
{report_markdown}
""".strip()
