"use client";

import React, { useState, useEffect } from "react";
import { X, Settings, Key, Check, Cpu, Zap, AlertCircle } from "lucide-react";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [provider, setProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("gpt-4o-mini");
  const [baseUrl, setBaseUrl] = useState("");
  const [hasApiKey, setHasApiKey] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchSettings();
    }
  }, [isOpen]);

  const fetchSettings = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/settings");
      if (res.ok) {
        const data = await res.json();
        setProvider(data.llm_provider || "openai");
        setModel(data.llm_model || "gpt-4o-mini");
        setBaseUrl(data.llm_base_url || "");
        setHasApiKey(data.has_api_key || false);
      }
    } catch (e) {
      console.error("Could not fetch settings", e);
    }
  };

  const handlePreset = (type: "openai" | "groq" | "ollama" | "gemini") => {
    if (type === "openai") {
      setProvider("openai");
      setModel("gpt-4o-mini");
      setBaseUrl("");
    } else if (type === "groq") {
      setProvider("groq");
      setModel("llama-3.3-70b-versatile");
      setBaseUrl("https://api.groq.com/openai/v1");
    } else if (type === "ollama") {
      setProvider("ollama");
      setModel("llama3");
      setBaseUrl("http://localhost:11434/v1");
    } else if (type === "gemini") {
      setProvider("gemini");
      setModel("gemini-1.5-flash");
      setBaseUrl("https://generativelanguage.googleapis.com/v1beta/openai/");
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setStatusMessage(null);
    try {
      const res = await fetch("http://localhost:8000/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          llm_provider: provider,
          llm_api_key: apiKey || undefined,
          llm_model: model,
          llm_base_url: baseUrl || undefined,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setHasApiKey(data.has_api_key);
        setStatusMessage("Settings saved! LLM client active.");
        setTimeout(() => onClose(), 1200);
      } else {
        setStatusMessage("Failed to save settings.");
      }
    } catch (err: any) {
      setStatusMessage(`Error: ${err?.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg bg-[#0e1628] border border-slate-800 rounded-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">LLM Provider & Intelligence Settings</h3>
              <p className="text-xs text-slate-400">Configure real LLM generation for personalized answers</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="p-6 space-y-4">
          {statusMessage && (
            <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center space-x-2">
              <Check className="w-4 h-4" />
              <span>{statusMessage}</span>
            </div>
          )}

          {/* Presets */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">
              Quick Provider Presets
            </label>
            <div className="grid grid-cols-4 gap-2">
              <button
                type="button"
                onClick={() => handlePreset("openai")}
                className={`py-1.5 px-2 rounded-lg text-[11px] font-medium border transition-colors ${
                  provider === "openai"
                    ? "bg-blue-600/20 border-blue-500 text-blue-300"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                OpenAI
              </button>
              <button
                type="button"
                onClick={() => handlePreset("groq")}
                className={`py-1.5 px-2 rounded-lg text-[11px] font-medium border transition-colors ${
                  provider === "groq"
                    ? "bg-blue-600/20 border-blue-500 text-blue-300"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                Groq (Free)
              </button>
              <button
                type="button"
                onClick={() => handlePreset("gemini")}
                className={`py-1.5 px-2 rounded-lg text-[11px] font-medium border transition-colors ${
                  provider === "gemini"
                    ? "bg-blue-600/20 border-blue-500 text-blue-300"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                Gemini
              </button>
              <button
                type="button"
                onClick={() => handlePreset("ollama")}
                className={`py-1.5 px-2 rounded-lg text-[11px] font-medium border transition-colors ${
                  provider === "ollama"
                    ? "bg-blue-600/20 border-blue-500 text-blue-300"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                Ollama (Local)
              </button>
            </div>
          </div>

          {/* API Key */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">
                API Key
              </label>
              {hasApiKey && (
                <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                  Active in memory
                </span>
              )}
            </div>
            <div className="relative">
              <Key className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={hasApiKey ? "•••••••••••••••••••••••• (Leave blank to keep current)" : "sk-... or gsk_..."}
                className="w-full pl-9 pr-3 py-2 text-xs bg-slate-900/90 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>
            <p className="text-[10px] text-slate-500 mt-1">
              For Ollama running locally, no API key is required.
            </p>
          </div>

          {/* Model Name */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Model Name
            </label>
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="gpt-4o-mini or llama-3.3-70b-versatile"
              className="w-full px-3 py-2 text-xs bg-slate-900/90 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
            />
          </div>

          {/* Base URL (Optional) */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              API Base URL (Optional / Custom Endpoints)
            </label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="e.g. https://api.groq.com/openai/v1 or http://localhost:11434/v1"
              className="w-full px-3 py-2 text-xs bg-slate-900/90 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono text-[11px]"
            />
          </div>

          {/* Footer Actions */}
          <div className="pt-2 flex items-center justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-4 py-2 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white transition-all shadow-md shadow-blue-600/30 flex items-center space-x-1.5"
            >
              {isSaving ? <span>Saving...</span> : <span>Save Settings</span>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
