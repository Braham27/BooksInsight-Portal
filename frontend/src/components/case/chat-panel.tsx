"use client";

import { useState, useRef, useEffect } from "react";
import { useChatHistory, useSendMessage } from "@/hooks/use-api";
import { Button, Input, Spinner } from "@/components/ui/primitives";
import { Send } from "lucide-react";
import type { ChatMessageResponse, InterviewProgress } from "@/lib/types";
import { cn } from "@/lib/utils";

export function ChatPanel({ caseId }: { caseId: string }) {
  const { data: history, isLoading } = useChatHistory(caseId);
  const send = useSendMessage(caseId);
  const [input, setInput] = useState("");
  const [progress, setProgress] = useState<InterviewProgress | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const handleSend = () => {
    const msg = input.trim();
    if (!msg) return;
    setInput("");
    send.mutate(msg, {
      onSuccess: (res) => {
        setProgress(res.progress);
      },
    });
  };

  return (
    <div className="flex h-full flex-col">
      {progress && (
        <div className="border-b bg-gray-50 px-4 py-2">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span>Step: {progress.current_step}</span>
            <span>{progress.percent_complete}% complete</span>
          </div>
          <div className="mt-1 h-1.5 w-full rounded-full bg-gray-200">
            <div
              className="h-1.5 rounded-full bg-brand-500 transition-all"
              style={{ width: `${progress.percent_complete}%` }}
            />
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading && (
          <div className="flex items-center gap-2 py-4">
            <Spinner />
            <span className="text-sm text-gray-500">Loading conversation...</span>
          </div>
        )}
        {history?.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={endRef} />
      </div>

      <div className="border-t p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your answer..."
            disabled={send.isPending}
          />
          <Button type="submit" disabled={send.isPending || !input.trim()}>
            {send.isPending ? (
              <Spinner className="h-4 w-4" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessageResponse }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-2 text-sm",
          isUser
            ? "bg-brand-600 text-white"
            : "bg-gray-100 text-gray-900"
        )}
      >
        {message.content}
      </div>
    </div>
  );
}
