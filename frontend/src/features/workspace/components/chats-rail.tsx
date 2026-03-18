"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { MessageSquare, Plus, Trash2 } from "lucide-react";

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
  onDeleteThread: (threadId: string) => void;
};

export function ChatsRail({ threads, activeThreadId, onSelectThread, onNewThread, onDeleteThread }: ChatsRailProps) {
  return (
    <aside className="flex h-full min-h-0 flex-col border-r border-stone-300/80 bg-stone-50/80">
      <div className="flex items-center justify-between border-b border-stone-300/80 px-3 py-2">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-700">Chats</p>
        <Button size="icon" variant="outline" className="h-8 w-8 rounded-md" onClick={onNewThread} aria-label="New chat" title="New chat">
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      <div className="min-h-0 flex-1 space-y-2 overflow-y-auto px-2 py-2">
        {threads.length === 0 ? (
          <p className="px-2 py-1 text-xs text-muted-foreground">No chats yet.</p>
        ) : (
          threads.map((thread) => (
            <div
              key={thread.id}
              className={cn(
                "flex items-center gap-1 rounded-lg border border-stone-300/80 bg-background p-1 transition hover:bg-stone-50",
                activeThreadId === thread.id ? "border-stone-400 bg-stone-100 shadow-sm" : "",
              )}
            >
              <button
                type="button"
                onClick={() => onSelectThread(thread.id)}
                className="min-w-0 flex-1 rounded-md px-2 py-1.5 text-left outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <div className="flex items-center gap-1.5">
                  <MessageSquare className="h-3.5 w-3.5 shrink-0 text-stone-500" />
                  <p className="truncate text-sm font-medium text-stone-900">{thread.title}</p>
                </div>
                <p className="mt-1 truncate text-[11px] text-stone-500">{new Date(thread.updatedAt).toLocaleString()}</p>
              </button>
              <Button
                type="button"
                size="icon"
                variant="ghost"
                className="h-7 w-7 shrink-0 rounded-md text-stone-600 hover:text-red-600"
                onClick={() => onDeleteThread(thread.id)}
                aria-label={`Delete chat ${thread.title}`}
                title="Delete chat"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}

