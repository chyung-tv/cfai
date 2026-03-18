"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { BookOpen, Brain, Database, EyeOff, FileText, Loader2, Plus, RotateCcw, Save, Scale } from "lucide-react";

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
  rules: Array<{ id: number; ruleText: string; isActive: boolean }>;
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
const TAB_ICONS: Record<ExplorerTab, typeof FileText> = {
  documents: FileText,
  skills: Brain,
  rules: Scale,
  memories: Database,
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
            <Button
              size="icon"
              variant="outline"
              className="h-8 w-8 rounded-md"
              onClick={onCreateDoc}
              aria-label="New document"
              title="New document"
            >
              <Plus className="h-4 w-4" />
            </Button>
          ) : null}
          <Button size="icon" variant="ghost" className="h-8 w-8 rounded-md" onClick={onHide} aria-label="Hide explorer" title="Hide explorer">
            <EyeOff className="h-4 w-4" />
          </Button>
        </div>
      </div>
      <div className="flex items-center gap-1 overflow-x-auto border-b border-stone-300/80 px-2 py-2">
        {(Object.keys(TAB_LABELS) as ExplorerTab[]).map((tab) => {
          const Icon = TAB_ICONS[tab];
          return (
            <Button
              key={tab}
              type="button"
              size="icon"
              variant={activeTab === tab ? "default" : "outline"}
              className="h-8 w-8 shrink-0 rounded-md"
              onClick={() => onSelectTab(tab)}
              aria-label={TAB_LABELS[tab]}
              title={TAB_LABELS[tab]}
            >
              <Icon className="h-4 w-4" />
            </Button>
          );
        })}
      </div>
      <div className="min-h-0 flex-1 space-y-2 overflow-y-auto px-2 py-2">
        {activeTab === "documents" ? (
          <div className="space-y-2 rounded-lg border border-stone-300/80 bg-background p-2">
            <div className="flex items-center gap-2">
              <Button
                size="icon"
                variant="outline"
                className="h-8 w-8"
                onClick={onCommitSnapshot}
                disabled={committingSnapshot}
                aria-label={committingSnapshot ? "Committing snapshot" : "Commit snapshot"}
                title={committingSnapshot ? "Committing..." : "Commit snapshot"}
              >
                {committingSnapshot ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              </Button>
              <Button
                size="icon"
                variant="outline"
                className="h-8 w-8"
                onClick={onRestoreSnapshot}
                disabled={!selectedSnapshotId || restoringSnapshot}
                aria-label={restoringSnapshot ? "Restoring snapshot" : "Restore snapshot"}
                title={restoringSnapshot ? "Restoring..." : "Restore snapshot"}
              >
                {restoringSnapshot ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
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
              <Button
                size="icon"
                variant="outline"
                className="h-8 w-8"
                onClick={onAddRule}
                disabled={!ruleInput.trim()}
                aria-label="Add rule"
                title="Add rule"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <div className="max-h-20 space-y-1 overflow-y-auto rounded-md border border-stone-300/80 p-2">
              {rules.length === 0 ? (
                <p className="text-[11px] text-muted-foreground">No rules yet.</p>
              ) : (
                rules.map((rule) => (
                  <p key={rule.id} className="truncate text-[11px] text-stone-700">
                    - [{rule.isActive ? "active" : "inactive"}] {rule.ruleText}
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
          <p className="px-2 pt-2 text-[11px] text-muted-foreground">
            <BookOpen className="mr-1 inline h-3.5 w-3.5 align-text-bottom" />
            Deleted skill rows may reappear after reseed/startup.
          </p>
        ) : null}
      </div>
    </aside>
  );
}

