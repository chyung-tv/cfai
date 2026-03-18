"use client";

import { useEffect, useRef, type RefObject } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { Loader2, Send } from "lucide-react";

export type ChatMessage = {
  id: number | string;
  role: "user" | "assistant" | "system";
  content: string;
  createdAt: string;
  pending?: boolean;
};

type ChatPaneProps = {
  messages: ChatMessage[];
  composerValue: string;
  submitting: boolean;
  onComposerChange: (value: string) => void;
  onSubmit: () => void;
  composerRef?: RefObject<HTMLInputElement | null>;
};

export function ChatPane({
  messages,
  composerValue,
  submitting,
  onComposerChange,
  onSubmit,
  composerRef,
}: ChatPaneProps) {
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages.length]);

  return (
    <section className="flex h-full min-h-0 flex-col bg-stone-50/40">
      <div className="border-b border-stone-300/80 px-3 py-2">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-700">Chat</p>
      </div>

      <div ref={listRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-3">
        {messages.length === 0 ? (
          <p className="text-sm text-muted-foreground">Start a conversation to propose document edits.</p>
        ) : (
          messages.map((item) => (
            <div
              key={item.id}
              className={cn(
                "max-w-[94%] rounded-xl border border-stone-300/80 p-3 shadow-sm",
                item.role === "user" ? "ml-auto bg-stone-100" : "bg-background",
              )}
            >
              <div className="mb-1 flex items-center justify-between gap-2">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-stone-600">{item.role}</p>
                <p className="text-[11px] text-stone-500">{new Date(item.createdAt).toLocaleTimeString()}</p>
              </div>
              <p className={cn("whitespace-pre-wrap text-sm leading-6", item.pending ? "italic text-stone-500" : "text-stone-900")}>
                {item.content}
              </p>
            </div>
          ))
        )}
      </div>

      <div className="sticky bottom-0 border-t border-stone-300/80 bg-background/95 px-3 py-2 backdrop-blur">
        <div className="flex items-center gap-2">
          <Input
            ref={composerRef}
            placeholder="Message the copilot..."
            value={composerValue}
            onChange={(event) => onComposerChange(event.target.value)}
            className="h-10 rounded-lg border-stone-300/80 bg-background"
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                onSubmit();
              }
            }}
          />
          <Button
            size="icon"
            className="h-10 w-10 rounded-lg"
            onClick={onSubmit}
            disabled={submitting || !composerValue.trim()}
            aria-label={submitting ? "Sending message" : "Send message"}
            title={submitting ? "Sending..." : "Send"}
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </section>
  );
}

