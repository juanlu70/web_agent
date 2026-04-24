"use client";

import { useRef, useEffect } from "react";
import { Message } from "@/lib/types";
import MessageBubble from "./MessageBubble";
import { Globe, Square } from "lucide-react";

interface ChatAreaProps {
  messages: Message[];
  isTyping: boolean;
  onStop?: () => void;
  model?: string;
}

export default function ChatArea({ messages, isTyping, onStop, model }: ChatAreaProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-4">
        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-[#ab68ff] text-white">
          <Globe size={32} />
        </div>
        <h1 className="mb-2 text-2xl font-semibold text-zinc-800 dark:text-zinc-100">Web Agent</h1>
        <p className="max-w-md text-center text-sm text-zinc-500 dark:text-zinc-400">
          Ask me anything. I&apos;ll search the web, analyze files, or answer from my own knowledge.
          {model && <span className="block mt-1 text-xs text-zinc-400">Model: {model}</span>}
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {isTyping && (
        <div className="flex gap-4 px-4 py-6 bg-[#f4f4f4] dark:bg-[#2a2a2a]">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#ab68ff] text-white">
            <Globe size={18} />
          </div>
          <div className="flex items-center gap-3">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Searching...</p>
            {onStop && (
              <button
                onClick={onStop}
                className="flex items-center gap-1 rounded-lg border border-zinc-300 bg-white px-3 py-1 text-xs font-medium text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
              >
                <Square size={10} className="fill-current" />
                Stop
              </button>
            )}
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}