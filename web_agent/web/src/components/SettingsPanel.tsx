"use client";

import { useState, useEffect, useCallback } from "react";
import { X, Sun, Moon, Monitor } from "lucide-react";
import { useTheme } from "@/lib/useTheme";
import { getServerConfig, healthCheck, setServerUrl } from "@/lib/api";

interface SettingsPanelProps {
  onClose: () => void;
}

export default function SettingsPanel({ onClose }: SettingsPanelProps) {
  const { theme, setTheme } = useTheme();
  const [serverUrl, setLocalServerUrl] = useState(() => {
    if (typeof window === "undefined") return "http://127.0.0.1:8400";
    return localStorage.getItem("web_agent_server") || "http://127.0.0.1:8400";
  });
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [connected, setConnected] = useState(false);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkConnection = useCallback(async () => {
    setChecking(true);
    setError(null);
    try {
      const health = await healthCheck();
      setConnected(true);
      setSelectedModel(health.model || "");
      const config = await getServerConfig();
      const modelList: string[] = [];
      const ollamaModel = config.ollama_model as string | undefined;
      const llmModel = config.llm_model as string | undefined;
      if (ollamaModel) modelList.push(ollamaModel);
      if (llmModel) modelList.push(llmModel);
      setModels(modelList);
    } catch {
      setConnected(false);
      setError("Cannot connect to server");
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    checkConnection();
  }, [checkConnection]);

  const handleServerChange = (url: string) => {
    setLocalServerUrl(url);
    setServerUrl(url);
  };

  const themeOptions: { value: "light" | "dark" | "system"; label: string; icon: React.ReactNode }[] = [
    { value: "light", label: "Light", icon: <Sun size={16} /> },
    { value: "dark", label: "Dark", icon: <Moon size={16} /> },
    { value: "system", label: "System", icon: <Monitor size={16} /> },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="mx-4 w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-[#2a2a2a]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-800 dark:text-zinc-100">Settings</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-700 dark:hover:text-zinc-300"
          >
            <X size={20} />
          </button>
        </div>

        <div className="space-y-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Theme
            </label>
            <div className="flex gap-2">
              {themeOptions.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setTheme(opt.value)}
                  className={`flex flex-1 items-center justify-center gap-1.5 rounded-xl border px-3 py-2 text-sm transition ${
                    theme === opt.value
                      ? "border-[#ab68ff] bg-[#ab68ff]/10 text-[#ab68ff] dark:border-[#ab68ff] dark:text-[#ab68ff]"
                      : "border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800"
                  }`}
                >
                  {opt.icon}
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Server URL
            </label>
            <input
              type="text"
              value={serverUrl}
              onChange={(e) => handleServerChange(e.target.value)}
              className="w-full rounded-xl border border-zinc-300 bg-zinc-50 px-3 py-2 text-sm outline-none focus:border-[#ab68ff] dark:border-zinc-600 dark:bg-[#1a1a1a] dark:text-zinc-200"
              placeholder="http://127.0.0.1:8400"
            />
          </div>

          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Connection
              </label>
              <span
                className={`text-xs ${
                  connected ? "text-green-500" : error ? "text-red-400" : "text-zinc-400"
                }`}
              >
                {checking ? "Checking..." : connected ? "Connected" : error || "Disconnected"}
              </span>
            </div>
            <button
              onClick={checkConnection}
              disabled={checking}
              className="w-full rounded-xl border border-zinc-300 px-3 py-2 text-sm transition hover:bg-zinc-50 dark:border-zinc-600 dark:hover:bg-zinc-800 dark:text-zinc-300"
            >
              {checking ? "Checking..." : "Test Connection"}
            </button>
          </div>

          {connected && models.length > 0 && (
            <div>
              <label className="mb-1.5 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Active Model
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full rounded-xl border border-zinc-300 bg-zinc-50 px-3 py-2 text-sm outline-none focus:border-[#ab68ff] dark:border-zinc-600 dark:bg-[#1a1a1a] dark:text-zinc-200"
              >
                {models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-zinc-400">
                Model is configured on the server via config.yaml. This shows the current active model.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}