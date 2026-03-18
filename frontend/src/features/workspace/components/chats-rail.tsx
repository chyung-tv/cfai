"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type ThreadItem = {
  id: string;
  title: string;
  updatedAt: string;
};

type ChatsRailProps = {
  threads: ThreadItem[];
  activeThreadId: string | null;
  onSelectThread: (threadId: string) => void;
  onNewThread: () => void;
};

export function ChatsRail({ threads, activeThreadId, onSelectThread, onNewThread }: ChatsRailProps) {
  return (
    <aside className="flex h-full min-h-0 flex-col border-r border-stone-300/80 bg-stone-50/80">
      <div className="flex items-center justify-between border-b border-stone-300/80 px-3 py-2">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-700">Chats</p>
        <Button size="sm" variant="outline" className="h-8 rounded-md px-2 text-xs" onClick={onNewThread}>
          New
        </Button>
      </div>
      <div className="min-h-0 flex-1 space-y-2 overflow-y-auto px-2 py-2">
        {threads.length === 0 ? (
          <p className="px-2 py-1 text-xs text-muted-foreground">No chats yet.</p>
        ) : (
          threads.map((thread) => (
            <button
              key={thread.id}
              type="button"
              onClick={() => onSelectThread(thread.id)}
              className={cn(
                "w-full rounded-lg border border-stone-300/80 bg-background px-3 py-2 text-left transition hover:bg-stone-50",
                activeThreadId === thread.id ? "border-stone-400 bg-stone-100 shadow-sm" : "",
              )}
            >
              <p className="truncate text-sm font-medium text-stone-900">{thread.title}</p>
              <p className="mt-1 text-[11px] text-stone-500">{new Date(thread.updatedAt).toLocaleString()}</p>
            </button>
          ))
        )}
      </div>
    </aside>
  );
}

