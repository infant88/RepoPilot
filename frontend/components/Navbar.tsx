"use client";

import React from "react";
import { GitBranch, Terminal, Shield, Cpu, RefreshCw, BarChart2, Plus, Github, Settings } from "lucide-react";

interface NavbarProps {
  currentRepo: any;
  onOpenConnectModal: () => void;
  onOpenEvalModal: () => void;
  onOpenSettingsModal: () => void;
  onRefreshIndex: () => void;
  isIndexing: boolean;
}

export default function Navbar({
  currentRepo,
  onOpenConnectModal,
  onOpenEvalModal,
  onOpenSettingsModal,
  onRefreshIndex,
  isIndexing,
}: NavbarProps) {
  return (
    <header className="h-14 border-b border-slate-800 bg-[#0d1322]/90 backdrop-blur-md px-4 flex items-center justify-between sticky top-0 z-30">
      {/* Brand & Logo */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 shadow-lg shadow-blue-500/20 text-white font-black text-sm">
          RP
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-sm tracking-wide bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              RepoPilot
            </span>
            <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Copilot v1.0
            </span>
          </div>
        </div>

        {/* Current Repository Pill */}
        {currentRepo && (
          <div className="hidden md:flex items-center space-x-2 pl-4 border-l border-slate-800 text-xs text-slate-300">
            <span className="text-slate-400 font-medium">Repository:</span>
            <span className="font-semibold text-slate-100 bg-slate-800/60 px-2 py-0.5 rounded border border-slate-700/50">
              {currentRepo.full_name}
            </span>
            <div className="flex items-center space-x-1 text-slate-400 bg-slate-900/60 px-2 py-0.5 rounded border border-slate-800">
              <GitBranch className="w-3 h-3 text-cyan-400" />
              <span>{currentRepo.current_branch || "main"}</span>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center space-x-2.5">
        {/* Index Status Badge */}
        {currentRepo && (
          <div className="flex items-center space-x-2 px-2.5 py-1 rounded-full text-xs bg-slate-900/80 border border-slate-800">
            <span
              className={`w-2 h-2 rounded-full ${
                currentRepo.status === "COMPLETED"
                  ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]"
                  : currentRepo.status === "FAILED"
                  ? "bg-red-400"
                  : "bg-amber-400 animate-pulse"
              }`}
            />
            <span className="text-[11px] font-medium text-slate-300">
              {currentRepo.status} {currentRepo.progress_percentage ? `(${currentRepo.progress_percentage}%)` : ""}
            </span>
            <button
              onClick={onRefreshIndex}
              disabled={isIndexing}
              title="Re-index repository"
              className="text-slate-400 hover:text-slate-200 transition-colors ml-1"
            >
              <RefreshCw className={`w-3 h-3 ${isIndexing ? "animate-spin text-blue-400" : ""}`} />
            </button>
          </div>
        )}

        {/* Evaluation Dashboard Button */}
        <button
          onClick={onOpenEvalModal}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/60 transition-all shadow-sm"
        >
          <BarChart2 className="w-3.5 h-3.5 text-indigo-400" />
          <span>RAG Evaluation</span>
        </button>

        {/* LLM Settings */}
        <button
          onClick={onOpenSettingsModal}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors border border-slate-800"
          title="LLM Settings & API Keys"
        >
          <Settings className="w-4 h-4" />
        </button>

        {/* Connect GitHub Repo */}
        <button
          onClick={onOpenConnectModal}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-md shadow-blue-600/20 transition-all"
        >
          <Github className="w-3.5 h-3.5" />
          <span>Connect Repo</span>
        </button>
      </div>
    </header>
  );
}
