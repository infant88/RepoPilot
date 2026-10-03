"use client";

import React, { useState } from "react";
import { X, Play, CheckCircle2, AlertTriangle, Clock, Zap, DollarSign, Target, Award } from "lucide-react";
import { API_BASE } from "@/lib/api";

interface EvaluationModalProps {
  isOpen: boolean;
  onClose: () => void;
  repositoryId?: string | null;
}

export default function EvaluationModal({
  isOpen,
  onClose,
  repositoryId,
}: EvaluationModalProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [evalResult, setEvalResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleRunEvaluation = async () => {
    if (!repositoryId) {
      setError("Please select or index a repository first.");
      return;
    }
    setError(null);
    setIsRunning(true);
    try {
      const res = await fetch(`${API_BASE}/evaluations/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repository_id: repositoryId }),
      });
      if (!res.ok) {
        throw new Error(`Evaluation failed with status: ${res.status}`);
      }
      const data = await res.json();
      setEvalResult(data);
    } catch (err: any) {
      setError(err?.message || "Failed to run evaluation");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-3xl max-h-[90vh] bg-[#0c1220] border border-slate-800 rounded-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">RAG Evaluation & Benchmark Suite</h3>
              <p className="text-xs text-slate-400">Context Precision, Recall, Faithfulness, Relevance & Latency</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
              {error}
            </div>
          )}

          {/* Action Callout */}
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <div>
              <h4 className="text-xs font-semibold text-slate-200">Standard Test Benchmark (4 Test Cases)</h4>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Runs ground-truth queries (login 401, architecture, auth implementation, docker) and calculates metrics.
              </p>
            </div>
            <button
              onClick={handleRunEvaluation}
              disabled={isRunning || !repositoryId}
              className="px-4 py-2 rounded-lg text-xs font-semibold bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 disabled:opacity-50 text-white shadow-md shadow-indigo-600/20 flex items-center space-x-1.5 shrink-0"
            >
              {isRunning ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  <span>Evaluating...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run Benchmark</span>
                </>
              )}
            </button>
          </div>

          {/* Metrics Summary Cards */}
          {evalResult && (
            <div className="space-y-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Aggregate Benchmark Metrics</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <MetricCard
                  label="Context Precision"
                  value={`${(evalResult.context_precision * 100).toFixed(1)}%`}
                  sub="Relevance of retrieved chunks"
                  color="text-emerald-400"
                />
                <MetricCard
                  label="Context Recall"
                  value={`${(evalResult.context_recall * 100).toFixed(1)}%`}
                  sub="Expected sources captured"
                  color="text-blue-400"
                />
                <MetricCard
                  label="Faithfulness"
                  value={`${(evalResult.faithfulness * 100).toFixed(1)}%`}
                  sub="Evidence-grounded claims"
                  color="text-purple-400"
                />
                <MetricCard
                  label="Answer Relevance"
                  value={`${(evalResult.answer_relevance * 100).toFixed(1)}%`}
                  sub="Intent & query alignment"
                  color="text-cyan-400"
                />
              </div>

              {/* Latency & Cost */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs">
                  <div className="text-slate-400 flex items-center space-x-1 mb-1">
                    <Clock className="w-3.5 h-3.5 text-amber-400" />
                    <span>Avg Retrieval Latency</span>
                  </div>
                  <div className="text-sm font-bold text-slate-200">{evalResult.retrieval_latency_ms} ms</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs">
                  <div className="text-slate-400 flex items-center space-x-1 mb-1">
                    <Zap className="w-3.5 h-3.5 text-blue-400" />
                    <span>Tokens Processed</span>
                  </div>
                  <div className="text-sm font-bold text-slate-200">{evalResult.total_token_usage} tokens</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs">
                  <div className="text-slate-400 flex items-center space-x-1 mb-1">
                    <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Estimated Cost</span>
                  </div>
                  <div className="text-sm font-bold text-slate-200">${evalResult.estimated_cost_usd}</div>
                </div>
              </div>

              {/* Case-by-case table */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Test Case Results</h4>
                <div className="space-y-2">
                  {evalResult.case_results?.map((cr: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-lg bg-slate-900/50 border border-slate-800 text-xs">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-semibold text-slate-200">{cr.question}</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {cr.latency_ms} ms
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 mb-1">
                        <strong>Retrieved Sources:</strong> {cr.retrieved_sources?.join(", ") || "None"}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        <strong>Expected Sources:</strong> {cr.expected_sources?.join(", ") || "None"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, sub, color }: { label: string; value: string; sub: string; color: string }) {
  return (
    <div className="p-3 rounded-lg bg-slate-900/70 border border-slate-800 text-xs">
      <span className="text-[11px] text-slate-400 block mb-1">{label}</span>
      <span className={`text-xl font-black ${color} block`}>{value}</span>
      <span className="text-[10px] text-slate-500 block mt-0.5">{sub}</span>
    </div>
  );
}
