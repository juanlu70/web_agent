"use client";

import { Message } from "@/lib/types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { User, Bot } from "lucide-react";

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-4 px-4 py-6 ${isUser ? "bg-transparent" : "bg-[#f4f4f4] dark:bg-[#2a2a2a]"}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm ${
          isUser ? "bg-[#19c37d] text-white" : "bg-[#ab68ff] text-white"
        }`}
      >
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>
      <div className="min-w-0 flex-1">
        <p className="mb-1 text-xs font-semibold text-zinc-500 dark:text-zinc-400">
          {isUser ? "You" : "Web Agent"}
        </p>
        {message.files && message.files.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-1">
            {message.files.map((f, i) => (
              <span
                key={i}
                className="inline-flex items-center rounded bg-zinc-200 px-2 py-0.5 text-xs text-zinc-700 dark:bg-zinc-700 dark:text-zinc-300"
              >
                {f.split("/").pop()}
              </span>
            ))}
          </div>
        )}
        <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-1 prose-pre:my-2 prose-ul:my-1 prose-ol:my-1">
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          )}
        </div>
      </div>
    </div>
  );
}