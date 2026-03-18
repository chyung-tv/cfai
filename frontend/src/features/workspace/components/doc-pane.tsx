"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ExplorerEntityType } from "@/features/workspace/components/docs-rail";

type DocPaneProps = {
  title: string;
  entityType: ExplorerEntityType | null;
  entityId: string;
  document: { key: string; title: string; content: string; currentRevisionId: string | null } | null;
  draftContent: string;
  saving: boolean;
  deleting: boolean;
  canDelete: boolean;
  onDraftChange: (value: string) => void;
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
  saving,
  deleting,
  canDelete,
  onDraftChange,
  onSave,
  onDelete,
  onHide,
}: DocPaneProps) {
  const doc = document;
  const isDocument = entityType === "document";

  return (
    <section className="flex h-full min-h-0 flex-col bg-background">
      <div className="flex items-center justify-between border-b border-stone-300/80 px-3 py-2">
        <div className="min-w-0">
          <p className="truncate text-base font-semibold tracking-tight text-stone-900">{title || "No item selected"}</p>
          <p className="truncate text-[11px] text-stone-500">{entityType ? `${entityType}:${entityId}` : ""}</p>
        </div>
        <div className="flex items-center gap-2">
          {canDelete ? (
            <Button size="sm" variant="destructive" className="h-8 rounded-md px-2 text-xs" onClick={onDelete} disabled={deleting}>
              {deleting ? "Deleting..." : "Delete"}
            </Button>
          ) : null}
          <Button size="sm" variant="outline" className="h-8 rounded-md px-2 text-xs" onClick={onHide}>
            Hide
          </Button>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto bg-stone-50/50 px-3 py-3">
        <textarea
          value={draftContent}
          onChange={(event) => onDraftChange(event.target.value)}
          className="h-full min-h-72 w-full rounded-xl border border-stone-300/80 bg-background p-3 font-mono text-xs leading-6 outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          spellCheck={false}
        />
      </div>

      <div className="border-t border-stone-300/80 px-3 py-2">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <Badge variant="outline">{entityType || "none"}</Badge>
          <Button size="sm" variant="outline" className="h-8 rounded-md px-2 text-xs" onClick={onSave} disabled={saving || !entityType}>
            {saving ? "Saving..." : "Save"}
          </Button>
          {isDocument ? <Badge variant="outline">Head: {doc?.currentRevisionId ?? "none"}</Badge> : null}
        </div>
        <p className="text-xs text-muted-foreground">
          {isDocument ? "Document editor for selected workspace document." : "Markdown editor for explorer entity."}
        </p>
      </div>
    </section>
  );
}

