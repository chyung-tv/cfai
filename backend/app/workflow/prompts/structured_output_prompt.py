from __future__ import annotations


def build_structured_output_prompt(*, report_markdown: str) -> str:
    return f"""
You are a strict data normalization engine for equity research markdown.

Task:
- Convert the following markdown report into a single JSON object only.
- Do not include markdown fences or extra commentary.
- Preserve factual content; do not invent data.
- If a field is unavailable, use null for optional fields and an empty array when appropriate.
- Ensure required fields are present and non-empty when inferable from the report.

Required top-level keys:
- report_meta
- executive_summary
- company_profile
- management_profile
- industry_profile
- financial_profile
- recent_developments
- life_line
- gemini_verdict
- quality

Critical requirements:
- report_meta.ticker must be present.
- executive_summary.final_verdict must be present.
- financial_profile.projection.revenue_cagr_10y must be present.
- life_line.thrive_factor must be present.
- gemini_verdict.viewpoint_conditions must contain at least one item.
- quality.parser_version must be "v1-llm-normalizer".

Return JSON matching this conceptual shape:
{{
  "report_meta": {{
    "title": "string",
    "date": "string|null",
    "analyst_classification": "string|null",
    "subject": "string|null",
    "ticker": "string",
    "sector": "string|null",
    "recommendation_text": "string|null"
  }},
  "executive_summary": {{
    "summary_text": "string",
    "core_thesis_points": ["string"],
    "final_verdict": "string"
  }},
  "company_profile": {{
    "business_essence": "string|null",
    "value_proposition": "string|null",
    "segments": [{{"name":"string","description":"string|null","revenue_share_estimate":"string|null","growth_signal":"string|null"}}],
    "economic_moat": {{"rating":"string|null","drivers":["string"]}},
    "five_forces": [{{"force":"string","intensity":"string|null","rationale":"string|null"}}],
    "growth_drivers": ["string"],
    "decline_drivers": ["string"],
    "customer_choice_rationale": "string|null"
  }},
  "management_profile": {{
    "executives": [{{"name":"string","role":"string|null","impact":"string|null","compensation_notes":"string|null"}}],
    "incentive_alignment_summary": "string|null"
  }},
  "industry_profile": {{
    "market_structure":"string|null",
    "competitive_landscape":"string|null",
    "ecosystem_dependencies":["string"],
    "secular_growth_drivers":["string"],
    "secular_decline_drivers":["string"],
    "ten_year_outlook_summary":"string|null",
    "market_share_projection_notes":"string|null"
  }},
  "financial_profile": {{
    "capital_efficiency": {{
      "roe_5y":"string|null",
      "roic_5y":"string|null",
      "roce_5y":"string|null",
      "peer_context":"string|null"
    }},
    "projection": {{
      "revenue_cagr_10y":"string",
      "operating_margin_path":"string|null",
      "projection_table_rows":[{{"period":"string","revenue":"string|null","operating_margin":"string|null","notes":"string|null"}}]
    }},
    "assumptions":["string"]
  }},
  "recent_developments": {{
    "events_6m":[{{"event":"string","date_or_window":"string|null","impact":"string|null","confidence":"string|null"}}],
    "material_price_moves":[{{"magnitude":"string|null","direction":"string|null","driver":"string|null"}}]
  }},
  "life_line": {{
    "thrive_factor":"string",
    "break_condition":"string|null",
    "failure_impact":"string|null"
  }},
  "gemini_verdict": {{
    "decision":"string",
    "verdict_logic":"string|null",
    "viewpoint_conditions":[{{"viewpoint":"string","suitability":"string","rationale":"string|null"}}],
    "alternatives":[{{"name":"string","reason":"string|null"}}]
  }},
  "quality": {{
    "parser_version":"v1-llm-normalizer",
    "extraction_confidence":"string|null",
    "missing_fields":["string"]
  }}
}}

Report markdown:
{report_markdown}
""".strip()
