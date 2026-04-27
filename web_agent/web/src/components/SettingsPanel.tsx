"use client";

import { useState, useEffect, useCallback } from "react";
import { X, Sun, Moon, Monitor, Check } from "lucide-react";
import { useTheme } from "@/lib/useTheme";
import { getServerConfig, healthCheck, setServerUrl } from "@/lib/api";

interface SettingsPanelProps {
  onClose: () => void;
}

export default function SettingsPanel({ onClose }: SettingsPanelProps) {
  const { theme, setTheme } = useTheme();
  const [draftTheme, setDraftTheme] = useState(theme);
  const [serverUrl, setLocalServerUrl] = useState("http://127.0.0.1:8400");
  const [draftServerUrl, setDraftServerUrl] = useState("http://127.0.0.1:8400");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const savedUrl = localStorage.getItem("web_agent_server");
    if (savedUrl) {
      setLocalServerUrl(savedUrl);
      setDraftServerUrl(savedUrl);
    }
  }, []);

  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [connected, setConnected] = useState(false);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkConnection = useCallback(async (url?: string) => {
    setChecking(true);
    setError(null);
    if (url) setServerUrl(url);
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

  const hasChanges = draftTheme !== theme || draftServerUrl !== serverUrl;

  const handleApply = () => {
    if (draftTheme !== theme) setTheme(draftTheme);
    if (draftServerUrl !== serverUrl) {
      setLocalServerUrl(draftServerUrl);
      setServerUrl(draftServerUrl);
      checkConnection(draftServerUrl);
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
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
                  onClick={() => setDraftTheme(opt.value)}
                  className={`flex flex-1 items-center justify-center gap-1.5 rounded-xl border px-3 py-2 text-sm transition ${
                    draftTheme === opt.value
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
              value={draftServerUrl}
              onChange={(e) => setDraftServerUrl(e.target.value)}
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
              onClick={() => checkConnection(draftServerUrl)}
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
                Model is configured on the server via config.yaml.
              </p>
            </div>
          )}
        </div>

        <div className="mt-6 flex items-center gap-3">
          <button
            onClick={handleApply}
            disabled={!hasChanges}
            className={`flex-1 rounded-xl py-2.5 text-sm font-medium transition ${
              hasChanges
                ? "bg-[#ab68ff] text-white hover:bg-[#9a55e0]"
                : "bg-zinc-100 text-zinc-400 dark:bg-zinc-800 dark:text-zinc-500"
            }`}
          >
            {saved ? (
              <span className="inline-flex items-center gap-1.5">
                <Check size={14} /> Applied
              </span>
            ) : (
              "Apply"
            )}
          </button>
          <button
            onClick={onClose}
            className="rounded-xl border border-zinc-300 px-4 py-2.5 text-sm font-medium text-zinc-600 transition hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}