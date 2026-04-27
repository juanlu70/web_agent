"use client";

import { useState, useCallback } from "react";
import { Menu, Settings } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import ChatArea from "@/components/ChatArea";
import ChatInput from "@/components/ChatInput";
import ConnectionStatus from "@/components/ConnectionStatus";
import SettingsPanel from "@/components/SettingsPanel";
import { useThreads } from "@/lib/useThreads";
import { HistoryEntry } from "@/lib/types";

export default function Home() {
  const {
    threads,
    activeThread,
    activeThreadId,
    setActiveThreadId,
    createThread,
    deleteThread,
    sendMessage,
    stopGeneration,
    loadHistoryEntry,
    isTyping,
  } = useThreads();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showSettings, setShowSettings] = useState(false);

  const hasMessages = (activeThread?.messages.length ?? 0) > 0;

  const handleSend = useCallback(
    async (query: string, deep: boolean, filePaths?: string[]) => {
      let threadId = activeThreadId;
      if (!threadId) {
        const thread = createThread();
        threadId = thread.id;
      }
      await sendMessage(threadId, query, deep, filePaths);
    },
    [activeThreadId, createThread, sendMessage]
  );

  const handleRerun = useCallback(
    (entry: HistoryEntry) => {
      loadHistoryEntry(entry);
    },
    [loadHistoryEntry]
  );

  return (
    <div className="flex h-screen bg-white dark:bg-[#1a1a1a]">
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      <div
        className={`fixed inset-y-0 left-0 z-50 transform transition-transform md:relative md:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <Sidebar
          threads={threads}
          activeThreadId={activeThreadId}
          onSelectThread={(id) => {
            setActiveThreadId(id);
          }}
          onNewThread={() => createThread()}
          onDeleteThread={deleteThread}
          onClose={() => setSidebarOpen(false)}
          onRerun={handleRerun}
        />
      </div>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-zinc-200 px-3 py-2 dark:border-zinc-800">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="rounded-lg p-2 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
            >
              <Menu size={20} />
            </button>
            <h1 className="text-sm font-semibold text-zinc-800 dark:text-zinc-100">Web Agent</h1>
          </div>
          <div className="flex items-center gap-2">
            <ConnectionStatus />
            <button
              onClick={() => setShowSettings(true)}
              className="rounded-lg p-2 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
              title="Settings"
            >
              <Settings size={18} />
            </button>
          </div>
        </header>

        {!hasMessages ? (
          <div className="flex flex-1 flex-col items-center justify-center px-4">
            <ChatInput onSend={handleSend} isTyping={isTyping} centered />
          </div>
        ) : (
          <>
            <ChatArea
              messages={activeThread?.messages || []}
              isTyping={isTyping}
              onStop={stopGeneration}
            />
            <ChatInput onSend={handleSend} isTyping={isTyping} />
          </>
        )}
      </main>

      {showSettings && <SettingsPanel onClose={() => setShowSettings(false)} />}
    </div>
  );
}