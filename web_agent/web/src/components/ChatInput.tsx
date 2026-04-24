"use client";

import { useState, useRef, useCallback } from "react";
import { Paperclip, Search, X, ArrowUp } from "lucide-react";

interface ChatInputProps {
  onSend: (query: string, deep: boolean, filePaths?: string[]) => void;
  disabled?: boolean;
  isTyping?: boolean;
  centered?: boolean;
}

interface AttachedFile {
  name: string;
  path: string;
}

export default function ChatInput({ onSend, disabled, isTyping, centered }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [deep, setDeep] = useState(false);
  const [files, setFiles] = useState<AttachedFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAttach = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    if (!fileList) return;
    const newFiles: AttachedFile[] = [];
    for (let i = 0; i < fileList.length; i++) {
      const f = fileList[i];
      newFiles.push({ name: f.name, path: f.name });
    }
    setFiles((prev) => [...prev, ...newFiles]);
    e.target.value = "";
  }, []);

  const removeFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleSubmit = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed && files.length === 0) return;
    onSend(trimmed || "analyze these files", deep, files.length > 0 ? files.map((f) => f.path) : undefined);
    setInput("");
    setFiles([]);
  }, [input, deep, files, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  const isDisabled = disabled || isTyping;

  const inputBox = (
    <div className="w-full max-w-2xl mx-auto px-4">
      <div className="mb-2 flex flex-wrap gap-1.5">
        {files.map((f, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1 rounded-lg bg-zinc-100 px-2.5 py-1 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
          >
            {f.name}
            <button onClick={() => removeFile(i)} className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300">
              <X size={12} />
            </button>
          </span>
        ))}
      </div>

      <div className="flex items-end gap-2 rounded-2xl border border-zinc-300 bg-zinc-50 px-4 py-3 dark:border-zinc-700 dark:bg-[#2a2a2a]">
        <button
          onClick={handleAttach}
          className="shrink-0 rounded-lg p-1.5 text-zinc-500 hover:bg-zinc-200 hover:text-zinc-700 dark:hover:bg-zinc-700 dark:hover:text-zinc-300"
          title="Attach files"
        >
          <Paperclip size={18} />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileChange}
          accept=".txt,.md,.csv,.json,.py,.js,.ts,.html,.css,.xml,.yaml,.yml,.pdf,.docx"
        />

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Send a message..."
          disabled={isDisabled}
          rows={3}
          className="max-h-60 min-h-[72px] w-full flex-1 resize-none bg-transparent py-1 text-[15px] leading-relaxed outline-none placeholder:text-zinc-400 disabled:opacity-50"
        />

        <button
          onClick={() => setDeep(!deep)}
          className={`shrink-0 flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium transition ${
            deep
              ? "bg-[#ab68ff] text-white"
              : "bg-zinc-200 text-zinc-500 hover:bg-zinc-300 dark:bg-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-600"
          }`}
          title={deep ? "Deep search ON (50 results)" : "Deep search OFF (10 results)"}
        >
          <Search size={12} />
          Deep
        </button>

        <button
          onClick={handleSubmit}
          disabled={isDisabled || (!input.trim() && files.length === 0)}
          className="shrink-0 rounded-lg bg-[#19c37d] p-1.5 text-white transition hover:bg-[#1a9d68] disabled:opacity-30 disabled:hover:bg-[#19c37d]"
        >
          <ArrowUp size={18} />
        </button>
      </div>

      <p className="mt-1.5 text-center text-[11px] text-zinc-400">
        Web Agent can make mistakes. Verify important information.
      </p>
    </div>
  );

  if (centered) {
    return (
      <div className="flex flex-col items-center justify-center px-4">
        {inputBox}
      </div>
    );
  }

  return (
    <div className="border-t bg-white px-4 py-3 dark:border-zinc-800 dark:bg-[#1a1a1a]">
      {inputBox}
    </div>
  );
}