"use client";

import { useState, useEffect, useCallback } from "react";
import { Thread, HistoryEntry } from "@/lib/types";
import { getHistory } from "@/lib/api";
import { Plus, MessageSquare, Trash2, X, Clock, RotateCw } from "lucide-react";

interface SidebarProps {
  threads: Thread[];
  activeThreadId: string | null;
  onSelectThread: (id: string) => void;
  onNewThread: () => void;
  onDeleteThread: (id: string) => void;
  onClose: () => void;
  onRerun: (entry: HistoryEntry) => void;
}

export default function Sidebar({
  threads,
  activeThreadId,
  onSelectThread,
  onNewThread,
  onDeleteThread,
  onClose,
  onRerun,
}: SidebarProps) {
  const [tab, setTab] = useState<"chats" | "history">("chats");
  const [historyEntries, setHistoryEntries] = useState<HistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const data = await getHistory(50);
      setHistoryEntries(data.history || []);
    } catch {
      // ignore
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    if (tab === "history") loadHistory();
  }, [tab, loadHistory]);

  return (
    <aside className="flex h-full w-72 flex-col bg-[#171717] text-white">
      <div className="flex items-center gap-2 p-3">
        <button
          onClick={onNewThread}
          className="flex flex-1 items-center gap-2 rounded-lg border border-white/20 px-3 py-2 text-sm transition hover:bg-white/10"
        >
          <Plus size={16} />
          New chat
        </button>
        <button onClick={onClose} className="rounded-lg p-2 hover:bg-white/10 md:hidden">
          <X size={18} />
        </button>
      </div>

      <div className="flex border-b border-white/10">
        <button
          onClick={() => setTab("chats")}
          className={`flex-1 px-3 py-2 text-xs font-medium transition ${
            tab === "chats" ? "border-b-2 border-white text-white" : "text-white/50 hover:text-white/80"
          }`}
        >
          Chats
        </button>
        <button
          onClick={() => setTab("history")}
          className={`flex-1 px-3 py-2 text-xs font-medium transition ${
            tab === "history" ? "border-b-2 border-white text-white" : "text-white/50 hover:text-white/80"
          }`}
        >
          History
        </button>
      </div>

      {tab === "chats" && (
        <nav className="flex-1 overflow-y-auto px-2 py-1">
          {threads.length === 0 && (
            <p className="px-3 py-6 text-center text-xs text-white/40">No conversations yet</p>
          )}
          {threads.map((thread) => (
            <div
              key={thread.id}
              className={`group flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition cursor-pointer ${
                thread.id === activeThreadId ? "bg-white/15" : "hover:bg-white/8"
              }`}
              onClick={() => onSelectThread(thread.id)}
            >
              <MessageSquare size={16} className="shrink-0 opacity-60" />
              <span className="flex-1 truncate">{thread.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteThread(thread.id);
                }}
                className="hidden shrink-0 rounded p-1 text-white/50 hover:bg-white/10 hover:text-white group-hover:block"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </nav>
      )}

      {tab === "history" && (
        <nav className="flex-1 overflow-y-auto px-2 py-1">
          <button
            onClick={loadHistory}
            disabled={historyLoading}
            className="mb-2 flex w-full items-center justify-center gap-1.5 rounded-lg border border-white/20 px-3 py-1.5 text-xs transition hover:bg-white/10"
          >
            <RotateCw size={12} className={historyLoading ? "animate-spin" : ""} />
            Refresh
          </button>
          {historyEntries.length === 0 && !historyLoading && (
            <p className="px-3 py-6 text-center text-xs text-white/40">No history yet</p>
          )}
          {historyEntries.map((entry) => (
            <div
              key={entry.id}
              className="group mb-1 rounded-lg px-3 py-2 text-sm transition cursor-pointer hover:bg-white/8"
              onClick={() => onRerun(entry)}
            >
              <p className="truncate text-white/90">{entry.query}</p>
              <div className="mt-0.5 flex items-center gap-1.5 text-[10px] text-white/40">
                <Clock size={10} />
                <span>{new Date(entry.timestamp).toLocaleDateString()}</span>
                {entry.deep && (
                  <span className="rounded bg-[#ab68ff]/30 px-1 py-0.5 text-[#ab68ff]">deep</span>
                )}
                {entry.file_paths?.length > 0 && <span>{entry.file_paths.length} file(s)</span>}
              </div>
            </div>
          ))}
        </nav>
      )}
    </aside>
  );
}