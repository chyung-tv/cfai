import { describe, expect, it } from "vitest";
import {
  parseMemoryMarkdown,
  parseRuleMarkdown,
  parseSkillMarkdown,
  toMemorySummaryMarkdown,
} from "@/features/workspace/components/entity_markdown";

describe("entity_markdown adapters", () => {
  it("parses rule markdown body", () => {
    const parsed = parseRuleMarkdown(`# Rule 4

Keep replies concise and include risks.`);
    expect(parsed.ruleText).toContain("include risks");
  });

  it("parses memory markdown metadata and json", () => {
    const parsed = parseMemoryMarkdown(`# Memory 2

## Metadata
- key: profile.name
- type: identity
- confidence: 0.95
- rationale: explicitly stated

## Value (JSON)
\`\`\`json
{"name":"yung"}
\`\`\`
`);
    expect(parsed.key).toBe("profile.name");
    expect(parsed.value).toEqual({ name: "yung" });
    expect(parsed.confidence).toBe(0.95);
  });

  it("parses skill markdown list sections", () => {
    const parsed = parseSkillMarkdown(`# Skill documents_editing

## Metadata
- name: Documents Editing
- enabled: true

## Brief
Edit docs.

## Prompt
Use tools carefully.

## Allowed Tools
- create_document
- edit_document

## Required Order
- create_document

## Blocked Combinations
- create_document -> run_research
`);
    expect(parsed.name).toBe("Documents Editing");
    expect(parsed.allowedTools).toEqual(["create_document", "edit_document"]);
    expect(parsed.requiredOrder).toEqual(["create_document"]);
    expect(parsed.blockedCombinations).toEqual([["create_document", "run_research"]]);
  });

  it("renders summary markdown header", () => {
    const output = toMemorySummaryMarkdown("User prefers concise replies.");
    expect(output).toContain("# Memory Summary");
    expect(output).toContain("concise");
  });
});
