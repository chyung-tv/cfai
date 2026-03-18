"use client";

import type { MemoryDetail, RuleItem, SkillDetail } from "@/shared/api/copilot_client";

export type ExplorerEntityType = "document" | "skill" | "rule" | "memory" | "memory_summary";

export function toRuleMarkdown(rule: RuleItem): string {
  return `# Rule ${rule.id}

${rule.ruleText}
`;
}

export function parseRuleMarkdown(markdown: string): { ruleText: string } {
  const content = markdown.replace(/^#\s*Rule[^\n]*\n?/i, "").trim();
  if (!content) {
    throw new Error("Rule body cannot be empty.");
  }
  return { ruleText: content };
}

export function toMemoryMarkdown(memory: MemoryDetail): string {
  return `# Memory ${memory.id}

## Metadata
- key: ${memory.key}
- type: ${memory.type}
- confidence: ${memory.confidence}
- rationale: ${memory.rationale}

## Value (JSON)
\`\`\`json
${JSON.stringify(memory.value, null, 2)}
\`\`\`
`;
}

export function parseMemoryMarkdown(markdown: string): {
  key: string;
  type: string;
  confidence: number;
  rationale: string;
  value: Record<string, unknown>;
} {
  const key = extractMeta(markdown, "key");
  const type = extractMeta(markdown, "type") || "preference";
  const confidenceRaw = extractMeta(markdown, "confidence") || "0.8";
  const rationale = extractMeta(markdown, "rationale") || "";
  const jsonBlock = extractJsonBlock(markdown);
  if (!key) {
    throw new Error("Memory key is required in metadata.");
  }
  let value: Record<string, unknown>;
  try {
    const parsed = JSON.parse(jsonBlock);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error("json object required");
    }
    value = parsed as Record<string, unknown>;
  } catch {
    throw new Error("Memory JSON block is invalid.");
  }
  const confidence = Number(confidenceRaw);
  if (Number.isNaN(confidence) || confidence < 0 || confidence > 1) {
    throw new Error("Memory confidence must be between 0 and 1.");
  }
  return {
    key: key.trim(),
    type: type.trim(),
    confidence,
    rationale: rationale.trim(),
    value,
  };
}

export function toSkillMarkdown(skill: SkillDetail): string {
  const blocked = skill.blockedCombinations.map((pair) => `- ${pair[0]} -> ${pair[1]}`).join("\n");
  return `# Skill ${skill.id}

## Metadata
- name: ${skill.name}
- enabled: ${skill.enabled}

## Brief
${skill.brief}

## Prompt
${skill.prompt}

## Allowed Tools
${skill.allowedTools.map((item) => `- ${item}`).join("\n")}

## Required Order
${skill.requiredOrder.map((item) => `- ${item}`).join("\n")}

## Blocked Combinations
${blocked}
`;
}

export function parseSkillMarkdown(markdown: string): Omit<SkillDetail, "id"> {
  const name = extractMeta(markdown, "name");
  const enabledRaw = extractMeta(markdown, "enabled");
  const brief = extractSection(markdown, "Brief");
  const prompt = extractSection(markdown, "Prompt");
  const allowedTools = extractListSection(markdown, "Allowed Tools");
  const requiredOrder = extractListSection(markdown, "Required Order");
  const blocked = extractListSection(markdown, "Blocked Combinations").flatMap((line) => {
    const parts = line.split("->").map((value) => value.trim());
    if (parts.length !== 2 || !parts[0] || !parts[1]) return [];
    return [[parts[0], parts[1]]];
  });
  if (!name) {
    throw new Error("Skill metadata requires a name.");
  }
  return {
    name: name.trim(),
    enabled: (enabledRaw || "true").trim().toLowerCase() === "true",
    brief: brief.trim(),
    prompt: prompt.trim(),
    allowedTools,
    requiredOrder,
    blockedCombinations: blocked,
  };
}

export function toMemorySummaryMarkdown(summary: string): string {
  return `# Memory Summary

${summary}
`;
}

export function parseMemorySummaryMarkdown(markdown: string): { summary: string } {
  const summary = markdown.replace(/^#\s*Memory Summary[^\n]*\n?/i, "").trim();
  return { summary };
}

function extractMeta(markdown: string, key: string): string {
  const pattern = new RegExp(`^-\\s*${escapeRegex(key)}:\\s*(.+)$`, "im");
  const match = markdown.match(pattern);
  return match?.[1]?.trim() || "";
}

function extractSection(markdown: string, title: string): string {
  const pattern = new RegExp(`##\\s*${escapeRegex(title)}\\s*\\n([\\s\\S]*?)(\\n##\\s|$)`, "i");
  const match = markdown.match(pattern);
  return match?.[1]?.trim() || "";
}

function extractListSection(markdown: string, title: string): string[] {
  const section = extractSection(markdown, title);
  if (!section) return [];
  return section
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("- "))
    .map((line) => line.slice(2).trim())
    .filter(Boolean);
}

function extractJsonBlock(markdown: string): string {
  const match = markdown.match(/```json\s*([\s\S]*?)```/i);
  if (match?.[1]) {
    return match[1].trim();
  }
  const fallback = extractSection(markdown, "Value (JSON)");
  return fallback.trim();
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
