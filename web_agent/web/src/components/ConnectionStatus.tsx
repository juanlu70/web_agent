"use client";

import { useState, useEffect } from "react";
import { healthCheck } from "@/lib/api";

export default function ConnectionStatus() {
  const [status, setStatus] = useState<"checking" | "connected" | "error">("checking");
  const [model, setModel] = useState("");

  useEffect(() => {
    healthCheck()
      .then((data) => {
        setStatus("connected");
        setModel(data.model || "");
      })
      .catch(() => setStatus("error"));
  }, []);

  if (status === "checking") {
    return <span className="text-xs text-zinc-400">Connecting...</span>;
  }
  if (status === "error") {
    return <span className="text-xs text-red-500">Offline</span>;
  }
  return (
    <span className="text-xs text-emerald-600 dark:text-emerald-400">
      {model ? model : "Connected"}
    </span>
  );
}