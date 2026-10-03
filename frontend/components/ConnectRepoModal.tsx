"use client";

import React, { useState } from "react";
import { X, Github, Sparkles, FolderGit2, Check, AlertCircle } from "lucide-react";

interface ConnectRepoModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnect: (url: string, branch: string) => Promise<void>;
  isLoading: boolean;
}

export default function ConnectRepoModal({
  isOpen,
  onClose,
  onConnect,
  isLoading,
}: ConnectRepoModalProps) {
  const [url, setUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      setError("Please enter a valid GitHub repository URL or select the demo repository.");
      return;
    }
    setError(null);
    try {
      await onConnect(url.trim(), branch.trim() || "main");
      onClose();
    } catch (err: any) {
      setError(err?.message || "Failed to connect repository");
    }
  };

  const handleSelectDemo = () => {
    setUrl("examples/sample-repo");
    setBranch("main");
    setError(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg bg-[#0e1628] border border-slate-800 rounded-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <FolderGit2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">Connect GitHub Repository</h3>
              <p className="text-xs text-slate-400">Index source code, branches, and documentation</p>
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
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Quick Demo Selector */}
          <div className="p-3 rounded-lg bg-gradient-to-r from-blue-900/20 to-indigo-900/20 border border-blue-500/20 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-blue-300 flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                <span>Demo Scenario Repository</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Sample FastAPI app with authentication, middleware, and 401 bug scenario.
              </p>
            </div>
            <button
              type="button"
              onClick={handleSelectDemo}
              className="px-2.5 py-1 text-xs font-medium rounded bg-blue-600 hover:bg-blue-500 text-white transition-colors shrink-0 ml-3"
            >
              Use Demo Repo
            </button>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              GitHub Repository URL or Path
            </label>
            <div className="relative">
              <Github className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://github.com/owner/repository or examples/sample-repo"
                className="w-full pl-9 pr-3 py-2 text-xs bg-slate-900/80 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Branch Name
            </label>
            <input
              type="text"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder="main"
              className="w-full px-3 py-2 text-xs bg-slate-900/80 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

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
              disabled={isLoading}
              className="px-4 py-2 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white transition-all shadow-md shadow-blue-600/30 flex items-center space-x-1.5"
            >
              {isLoading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  <span>Connecting & Indexing...</span>
                </>
              ) : (
                <span>Connect & Start Indexing</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
