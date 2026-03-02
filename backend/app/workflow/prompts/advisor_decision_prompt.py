from __future__ import annotations

import json


def build_advisor_decision_prompt(
    *,
    symbol: str,
    projection_years: int,
    optimistic_cagr_pct: float,
    median_cagr_pct: float,
    conservative_cagr_pct: float,
    audit_cases: list[dict],
    report_markdown: str,
) -> str:
    profile_inputs = json.dumps(
        [
            {"profile": "cash_preservation"},
            {"profile": "balanced_compounder"},
            {"profile": "capital_multiplier"},
        ],
        ensure_ascii=True,
    )
    case_inputs = json.dumps(
        [
            {"caseName": "optimistic", "requiredRevenueCagrPct": optimistic_cagr_pct},
            {"caseName": "median", "requiredRevenueCagrPct": median_cagr_pct},
            {"caseName": "conservative", "requiredRevenueCagrPct": conservative_cagr_pct},
        ],
        ensure_ascii=True,
    )
    audit_json = json.dumps(audit_cases, ensure_ascii=True)

    return f"""
You are an investment advisor decision engine for equity analysis.

Task:
- Produce profile-specific action advice grounded in the report and growth-likelihood audit.
- Return only one JSON object (no markdown, no commentary).

Entity:
- Symbol: {symbol}
- Horizon: {projection_years} years

Investor profiles and linked CAGR anchors:
{profile_inputs}

Reverse DCF cases to evaluate for EACH profile:
{case_inputs}

Audit growth-likelihood cases:
{audit_json}

Required output schema:
{{
  "symbol": "{symbol}",
  "projectionYears": {projection_years},
  "overallCall": "string",
  "profiles": [
    {{
      "profile": "cash_preservation|balanced_compounder|capital_multiplier",
      "profileSummary": "short framing for this investor type",
      "caseAdvisories": [
        {{
          "caseName": "optimistic|median|conservative",
          "requiredRevenueCagrPct": number,
          "action": "accumulate|hold|trim|avoid",
          "advice": "short concrete recommendation (1-2 sentences)",
          "reasoning": "detailed critical reasoning",
          "evidenceRefs": ["sec:Section", "sec:Section:Subsection"],
          "keyRisks": ["string"],
          "invalidateConditions": ["string"]
        }}
      ]
    }}
  ],
  "quality": {{
    "parserVersion": "v1-advisor-decision",
    "missingFields": ["string"],
    "warnings": ["string"]
  }}
}}

Rules:
- Output exactly 3 profiles, one per required profile, no duplicates.
- For each profile, output exactly 3 `caseAdvisories`: optimistic, median, conservative (once each).
- Use one discrete action only (`accumulate|hold|trim|avoid`) per profile-case.
- Keep `requiredRevenueCagrPct` aligned to the provided reverse DCF case values.
- `advice` must be short and concrete, max 2 sentences.
- `reasoning` must be critical and specific, not generic.
- Every profile-case must include non-empty `evidenceRefs` entries, each starting with `sec:`.
- Every profile-case must include at least 2 `keyRisks` and at least 2 `invalidateConditions`.
- Respect the growth-likelihood signals when selecting actions.
- Do not fabricate facts beyond provided inputs.
- `quality.parserVersion` must be `v1-advisor-decision`.

Report markdown:
{report_markdown}
""".strip()
