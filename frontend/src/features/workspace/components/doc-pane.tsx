"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ExplorerEntityType } from "@/features/workspace/components/docs-rail";
import { EyeOff, Loader2, Save, Trash2 } from "lucide-react";

type DocPaneProps = {
  title: string;
  entityType: ExplorerEntityType | null;
  entityId: string;
  document: { key: string; title: string; content: string; currentRevisionId: string | null } | null;
  draftContent: string;
  memoryValue: string;
  ruleIsActive: boolean;
  saving: boolean;
  deleting: boolean;
  canDelete: boolean;
  onDraftChange: (value: string) => void;
  onMemoryValueChange: (value: string) => void;
  onRuleIsActiveChange: (value: boolean) => void;
  onSave: () => void;
  onDelete: () => void;
  onHide: () => void;
};

export function DocPane({
  title,
  entityType,
  entityId,
  document,
  draftContent,
  memoryValue,
  ruleIsActive,
  saving,
  deleting,
  canDelete,
  onDraftChange,
  onMemoryValueChange,
  onRuleIsActiveChange,
  onSave,
  onDelete,
  onHide,
}: DocPaneProps) {
  const doc = document;
  const isDocument = entityType === "document";
  const isRule = entityType === "rule";
  const isMemory = entityType === "memory";

  return (
    <section className="flex h-full min-h-0 flex-col bg-background">
      <div className="flex items-center justify-between border-b border-stone-300/80 px-3 py-2">
        <div className="min-w-0">
          <p className="truncate text-base font-semibold tracking-tight text-stone-900">{title || "No item selected"}</p>
          <p className="truncate text-[11px] text-stone-500">{entityType ? `${entityType}:${entityId}` : ""}</p>
        </div>
        <div className="flex items-center gap-2">
          {canDelete ? (
            <Button
              size="icon"
              variant="destructive"
              className="h-8 w-8 rounded-md"
              onClick={onDelete}
              disabled={deleting}
              aria-label={deleting ? "Deleting item" : "Delete item"}
              title={deleting ? "Deleting..." : "Delete"}
            >
              {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
            </Button>
          ) : null}
          <Button size="icon" variant="outline" className="h-8 w-8 rounded-md" onClick={onHide} aria-label="Hide pane" title="Hide pane">
            <EyeOff className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto bg-stone-50/50 px-3 py-3">
        {isMemory ? (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">
              Edit memory value only. Key/type/confidence metadata is managed internally.
            </p>
            <textarea
              value={memoryValue}
              onChange={(event) => onMemoryValueChange(event.target.value)}
              className="h-full min-h-72 w-full rounded-xl border border-stone-300/80 bg-background p-3 text-sm leading-6 outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              spellCheck={false}
            />
          </div>
        ) : null}
        {isRule ? (
          <div className="space-y-3">
            <textarea
              value={draftContent}
              onChange={(event) => onDraftChange(event.target.value)}
              className="h-full min-h-72 w-full rounded-xl border border-stone-300/80 bg-background p-3 text-sm leading-6 outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              spellCheck={false}
            />
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant={ruleIsActive ? "default" : "outline"}
                className="h-8 rounded-md px-3 text-xs"
                onClick={() => onRuleIsActiveChange(!ruleIsActive)}
              >
                {ruleIsActive ? "Active" : "Inactive"}
              </Button>
              <p className="text-xs text-muted-foreground">Toggle whether this rule is applied during chat turns.</p>
            </div>
          </div>
        ) : null}
        {!isMemory && !isRule ? (
          <textarea
            value={draftContent}
            onChange={(event) => onDraftChange(event.target.value)}
            className="h-full min-h-72 w-full rounded-xl border border-stone-300/80 bg-background p-3 font-mono text-xs leading-6 outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            spellCheck={false}
          />
        ) : null}
      </div>

      <div className="border-t border-stone-300/80 px-3 py-2">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <Badge variant="outline">{entityType || "none"}</Badge>
          <Button
            size="icon"
            variant="outline"
            className="h-8 w-8 rounded-md"
            onClick={onSave}
            disabled={saving || !entityType}
            aria-label={saving ? "Saving item" : "Save item"}
            title={saving ? "Saving..." : "Save"}
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          </Button>
          {isDocument ? <Badge variant="outline">Head: {doc?.currentRevisionId ?? "none"}</Badge> : null}
        </div>
        <p className="text-xs text-muted-foreground">
          {isDocument
            ? "Document editor for selected workspace document."
            : isMemory
              ? "Memory value editor (metadata hidden)."
              : isRule
                ? "Rule editor with active toggle."
                : "Markdown editor for explorer entity."}
        </p>
      </div>
    </section>
  );
}

