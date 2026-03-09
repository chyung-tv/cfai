from __future__ import annotations

import json


def build_dynamic_schema_prompt(*, report_markdown: str) -> str:
    return f"""
You are a schema designer for equity research normalization.

Read the report and propose a compact dynamic schema that captures the most decision-useful fields.
Choose fields based on document content quality and downstream usefulness.

Return ONLY a JSON object with this shape:
{{
  "fields": [
    {{
      "name": "snake_case_field_name",
      "type": "string|number|boolean|array_string",
      "required": true_or_false,
      "description": "what this field means"
    }}
  ],
  "notes": "short explanation"
}}

Rules:
- 8 to 20 fields only.
- No nested object types in dynamic fields.
- Names must be unique and snake_case.
- Prefer fields tied to thesis, valuation, risk, and key assumptions.

Report markdown:
{report_markdown}
""".strip()


def build_dynamic_data_prompt(*, report_markdown: str, schema_fields: list[dict]) -> str:
    fields_json = json.dumps(schema_fields, ensure_ascii=True)
    return f"""
You are a data extractor for equity research normalization.

Using the provided schema fields, extract values from the report.
Return ONLY a JSON object with this exact top-level shape:
{{
  "base": {{
    "ticker": "string|null",
    "final_verdict": "string|null",
    "life_line_thrive_factor": "string|null"
  }},
  "dynamic_data": {{
    "...field_name_from_schema...": "value"
  }},
  "quality": {{
    "parser_version": "v2-dynamic-llm",
    "extraction_confidence": "high|medium|low",
    "missing_fields": ["field_name"]
  }}
}}

For dynamic_data:
- Use only keys listed in schema fields.
- Respect type requirements.
- If value is unavailable:
  - use null for optional required=false fields
  - use empty list for array_string
  - for required=true fields, include best-effort inferred value only if grounded in the report; otherwise set null and add to missing_fields.

Schema fields:
{fields_json}

Report markdown:
{report_markdown}
""".strip()


__all__ = ["build_dynamic_data_prompt", "build_dynamic_schema_prompt"]
