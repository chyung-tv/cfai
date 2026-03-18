"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export type ExplorerTab = "documents" | "skills" | "rules" | "memories";
export type ExplorerEntityType = "document" | "skill" | "rule" | "memory" | "memory_summary";

export type ExplorerItem = {
  id: string;
  title: string;
  subtitle?: string;
  entityType: ExplorerEntityType;
};

type DocsRailProps = {
  activeTab: ExplorerTab;
  activeItemId: string;
  itemsByTab: Record<ExplorerTab, ExplorerItem[]>;
  onSelectTab: (tab: ExplorerTab) => void;
  onSelectItem: (item: ExplorerItem) => void;
  onCreateDoc: () => void;
  snapshots: Array<{ id: string; message: string; createdAt: string; parentSnapshotId: string | null }>;
  selectedSnapshotId: string;
  committingSnapshot: boolean;
  restoringSnapshot: boolean;
  ruleInput: string;
  rules: Array<{ id: number; ruleText: string }>;
  onRuleInputChange: (value: string) => void;
  onAddRule: () => void;
  onCommitSnapshot: () => void;
  onSelectSnapshot: (snapshotId: string) => void;
  onRestoreSnapshot: () => void;
  onHide: () => void;
};

const TAB_LABELS: Record<ExplorerTab, string> = {
  documents: "Documents",
  skills: "Skills",
  rules: "Rules",
  memories: "Memories",
};

export function DocsRail({
  activeTab,
  activeItemId,
  itemsByTab,
  onSelectTab,
  onSelectItem,
  onCreateDoc,
  snapshots,
  selectedSnapshotId,
  committingSnapshot,
  restoringSnapshot,
  ruleInput,
  rules,
  onRuleInputChange,
  onAddRule,
  onCommitSnapshot,
  onSelectSnapshot,
  onRestoreSnapshot,
  onHide,
}: DocsRailProps) {
  const items = itemsByTab[activeTab] || [];
  return (
    <aside className="flex h-full min-h-0 flex-col border-l border-r border-stone-300/80 bg-stone-50/80">
      <div className="flex items-center justify-between border-b border-stone-300/80 px-3 py-2">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-700">Explorer</p>
        <div className="flex items-center gap-1">
          {activeTab === "documents" ? (
            <Button size="sm" variant="outline" className="h-8 rounded-md px-2 text-xs" onClick={onCreateDoc}>
              New
            </Button>
          ) : null}
          <Button size="sm" variant="ghost" className="h-8 rounded-md px-2 text-xs" onClick={onHide}>
            Hide
          </Button>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-1 border-b border-stone-300/80 px-2 py-2">
        {(Object.keys(TAB_LABELS) as ExplorerTab[]).map((tab) => (
          <Button
            key={tab}
            type="button"
            size="sm"
            variant={activeTab === tab ? "default" : "outline"}
            className="h-8 rounded-md text-xs"
            onClick={() => onSelectTab(tab)}
          >
            {TAB_LABELS[tab]}
          </Button>
        ))}
      </div>
      <div className="min-h-0 flex-1 space-y-2 overflow-y-auto px-2 py-2">
        {activeTab === "documents" ? (
          <div className="space-y-2 rounded-lg border border-stone-300/80 bg-background p-2">
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                className="h-8 px-2 text-xs"
                onClick={onCommitSnapshot}
                disabled={committingSnapshot}
              >
                {committingSnapshot ? "Committing..." : "Commit Snapshot"}
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-8 px-2 text-xs"
                onClick={onRestoreSnapshot}
                disabled={!selectedSnapshotId || restoringSnapshot}
              >
                {restoringSnapshot ? "Restoring..." : "Restore Snapshot"}
              </Button>
            </div>
            <p className="text-[10px] font-medium uppercase tracking-widest text-stone-600">Workspace Snapshot History</p>
            <div className="max-h-40 space-y-1 overflow-y-auto rounded-md border border-stone-300/80 bg-stone-50/40 p-2">
              {snapshots.length === 0 ? (
                <p className="text-[11px] text-muted-foreground">No workspace snapshots yet.</p>
              ) : (
                snapshots.map((snapshot, index) => {
                  const isSelected = selectedSnapshotId === snapshot.id;
                  const hasNext = index < snapshots.length - 1;
                  return (
                    <button
                      key={snapshot.id}
                      type="button"
                      onClick={() => onSelectSnapshot(snapshot.id)}
                      className={cn(
                        "relative w-full rounded-md border px-3 py-2 text-left text-xs transition",
                        isSelected ? "border-stone-500 bg-stone-100" : "border-stone-300/80 bg-background hover:bg-stone-50",
                      )}
                    >
                      <span className="absolute left-2 top-3 h-2 w-2 rounded-full bg-stone-600" />
                      {hasNext ? <span className="absolute left-[11px] top-5 h-6 w-px bg-stone-300" /> : null}
                      <div className="pl-4">
                        <p className="truncate font-medium text-stone-900">{snapshot.message || "Workspace snapshot"}</p>
                        <p className="truncate text-[11px] text-stone-500">{new Date(snapshot.createdAt).toLocaleString()}</p>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        ) : null}
        {activeTab === "rules" ? (
          <div className="space-y-2 rounded-lg border border-stone-300/80 bg-background p-2">
            <div className="flex gap-2">
              <Input
                placeholder="Add rule"
                value={ruleInput}
                onChange={(event) => onRuleInputChange(event.target.value)}
                className="h-8 text-xs"
              />
              <Button size="sm" variant="outline" className="h-8 px-2 text-xs" onClick={onAddRule} disabled={!ruleInput.trim()}>
                Add
              </Button>
            </div>
            <div className="max-h-20 space-y-1 overflow-y-auto rounded-md border border-stone-300/80 p-2">
              {rules.length === 0 ? (
                <p className="text-[11px] text-muted-foreground">No active rules.</p>
              ) : (
                rules.map((rule) => (
                  <p key={rule.id} className="truncate text-[11px] text-stone-700">
                    - {rule.ruleText}
                  </p>
                ))
              )}
            </div>
          </div>
        ) : null}
        {items.length === 0 ? (
          <p className="px-2 py-1 text-xs text-muted-foreground">No {TAB_LABELS[activeTab].toLowerCase()} yet.</p>
        ) : (
          items.map((item) => (
            <button
              key={`${item.entityType}:${item.id}`}
              type="button"
              onClick={() => onSelectItem(item)}
              className={cn(
                "w-full rounded-lg border border-stone-300/80 bg-background px-3 py-2 text-left text-sm transition hover:bg-stone-50",
                activeItemId === `${item.entityType}:${item.id}` ? "border-stone-400 bg-stone-100 shadow-sm" : "",
              )}
            >
              <p className="truncate text-sm font-medium text-stone-900">{item.title}</p>
              {item.subtitle ? <p className="mt-1 truncate text-[11px] text-stone-500">{item.subtitle}</p> : null}
            </button>
          ))
        )}
        {activeTab === "skills" ? (
          <p className="px-2 pt-2 text-[11px] text-muted-foreground">Deleted skill rows may reappear after reseed/startup.</p>
        ) : null}
      </div>
    </aside>
  );
}

