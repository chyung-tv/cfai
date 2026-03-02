from __future__ import annotations


def build_structured_output_prompt(*, report_markdown: str) -> str:
    return f"""
You are a strict equity-research parser for UI rendering.

Task:
- Convert the report into ONE JSON object for the UI sections below.
- Return JSON only. No markdown fences. No extra commentary.
- Do not invent facts; rely only on report content.
- Use null for missing optional scalars and [] for missing lists.

Critical requirements:
- executiveSummary.summary must be present.
- businessQuality.qualityTier must be present.
- quality.parserVersion must be "v2-ui-structured-output".

Return JSON with EXACTLY this shape:
{{
  "schemaVersion": "v2-ui-structured-output",
  "executiveSummary": {{
    "summary": "string",
    "lifeline": "string|null",
    "evidenceRefs": ["sec:Section", "sec:Section:Subsection"]
  }},
  "managementProfile": {{
    "leadershipSummary": "string|null",
    "keyPeople": [
      {{
        "name": "string",
        "role": "string|null",
        "impact": "string|null"
      }}
    ],
    "evidenceRefs": ["sec:Section"]
  }},
  "businessQuality": {{
    "qualityTier": "Tier 1|Tier 2|Tier 3|string",
    "moat": ["string"],
    "evidenceRefs": ["sec:Section"]
  }},
  "industryProfile": {{
    "marketStructure": "string|null",
    "position": "string|null",
    "positionRationale": "string|null",
    "evidenceRefs": ["sec:Section"]
  }},
  "recentDevelopments": {{
    "items": [
      {{
        "event": "string",
        "timing": "string|null",
        "impact": "string|null",
        "confidence": "string|null",
        "evidenceRefs": ["sec:Section"]
      }}
    ],
    "evidenceRefs": ["sec:Section"]
  }},
  "quality": {{
    "parserVersion":"v2-ui-structured-output",
    "extractionConfidence":"high|medium|low|null",
    "missingFields":["string"],
    "warnings":["string"]
  }}
}}

Reference format:
- Evidence refs should begin with "sec:".
- Prefer section anchors like "sec:ExecutiveSummary", "sec:ManagementProfile", "sec:RecentDevelopments".

Report markdown:
{report_markdown}
""".strip()
