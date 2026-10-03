"use client";

import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Send,
  Sparkles,
  Bot,
  User,
  Shield,
  Bug,
  Cpu,
  Terminal,
  FileText,
  FileCode,
  Layers,
  ChevronRight,
  ExternalLink,
  Trash2,
  GitBranch,
  RefreshCw,
  FolderTree,
  AlertCircle,
  HelpCircle,
} from "lucide-react";

import Navbar from "@/components/Navbar";
import FileTree, { FileTreeNode } from "@/components/FileTree";
import CodeViewer from "@/components/CodeViewer";
import ConnectRepoModal from "@/components/ConnectRepoModal";
import EvaluationModal from "@/components/EvaluationModal";
import SettingsModal from "@/components/SettingsModal";

const API_BASE = "http://localhost:8000/api";

interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  citations?: any[];
  agent_name?: string;
  intent?: string;
  retrieval_latency_ms?: number;
  generation_latency_ms?: number;
}

export default function Home() {
  const [repositories, setRepositories] = useState<any[]>([]);
  const [currentRepo, setCurrentRepo] = useState<any>(null);
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeAgentStatus, setActiveAgentStatus] = useState<string | null>(null);

  // Monaco Viewer State
  const [isCodeViewerOpen, setIsCodeViewerOpen] = useState(false);
  const [activeFilePath, setActiveFilePath] = useState<string | null>(null);
  const [activeFileContent, setActiveFileContent] = useState<string>("");
  const [highlightRange, setHighlightRange] = useState<{ startLine: number; endLine: number } | null>(null);

  // Modals
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false);
  const [isEvalModalOpen, setIsEvalModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch initial repositories on load
  useEffect(() => {
    fetchRepositories();
  }, []);

  // Poll indexing status when repository is indexing
  useEffect(() => {
    if (!currentRepo || currentRepo.status === "COMPLETED" || currentRepo.status === "FAILED") {
      return;
    }
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/repositories/${currentRepo.id}/index-status`);
        if (res.ok) {
          const statusData = await res.json();
          setCurrentRepo((prev: any) => ({ ...prev, ...statusData }));
          if (statusData.status === "COMPLETED") {
            loadFileTree(currentRepo.id);
            fetchRepositories();
          }
        }
      } catch (err) {
        console.error("Error polling index status", err);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [currentRepo]);

  // Scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeAgentStatus]);

  const fetchRepositories = async () => {
    try {
      const res = await fetch(`${API_BASE}/repositories`);
      if (res.ok) {
        const data = await res.json();
        setRepositories(data);
        if (data.length > 0 && !currentRepo) {
          setCurrentRepo(data[0]);
          loadFileTree(data[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch repositories", err);
    }
  };

  const loadFileTree = async (repoId: string) => {
    try {
      const res = await fetch(`${API_BASE}/repositories/${repoId}/files-tree`);
      if (res.ok) {
        const data = await res.json();
        setFileTree(data);
      }
    } catch (err) {
      console.error("Failed to load file tree", err);
    }
  };

  const handleSelectRepository = (repo: any) => {
    setCurrentRepo(repo);
    loadFileTree(repo.id);
    setMessages([]);
    setIsCodeViewerOpen(false);
  };

  const handleConnectRepo = async (url: string, branch: string) => {
    setIsConnecting(true);
    try {
      const res = await fetch(`${API_BASE}/repositories`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, branch }),
      });
      if (!res.ok) {
        throw new Error(`Failed with status: ${res.status}`);
      }
      const newRepo = await res.json();
      setCurrentRepo(newRepo);
      fetchRepositories();
    } finally {
      setIsConnecting(false);
    }
  };

  const handleRefreshIndex = async () => {
    if (!currentRepo) return;
    try {
      const res = await fetch(`${API_BASE}/repositories/${currentRepo.id}/index`, {
        method: "POST",
      });
      if (res.ok) {
        const updated = await res.json();
        setCurrentRepo((prev: any) => ({ ...prev, ...updated }));
      }
    } catch (err) {
      console.error("Failed to trigger re-index", err);
    }
  };

  const handleOpenFile = async (filePath: string, range?: { startLine: number; endLine: number } | null) => {
    if (!currentRepo) return;
    try {
      const res = await fetch(`${API_BASE}/repositories/${currentRepo.id}/files-content?path=${encodeURIComponent(filePath)}`);
      if (res.ok) {
        const data = await res.json();
        setActiveFilePath(filePath);
        setActiveFileContent(data.content || "");
        setHighlightRange(range || null);
        setIsCodeViewerOpen(true);
      }
    } catch (err) {
      console.error("Failed to open file", err);
    }
  };

  const handleSendMessage = async (queryText?: string) => {
    const text = queryText || inputQuery;
    if (!text.trim() || !currentRepo || isStreaming) return;

    setInputQuery("");
    const userMessage: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setIsStreaming(true);
    setActiveAgentStatus("Classifying intent & searching code chunks...");

    // Placeholder assistant message for streaming
    const assistantIndex = messages.length + 1;
    const initialAssistantMsg: Message = {
      role: "assistant",
      content: "",
      citations: [],
    };
    setMessages((prev) => [...prev, initialAssistantMsg]);

    try {
      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repository_id: currentRepo.id,
          message: text,
        }),
      });

      if (!response.body) throw new Error("No response stream");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;
            try {
              const event = JSON.parse(jsonStr);

              if (event.type === "agent_status") {
                setActiveAgentStatus(event.message || event.status);
              } else if (event.type === "citations") {
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  if (lastIdx >= 0 && updated[lastIdx].role === "assistant") {
                    updated[lastIdx] = {
                      ...updated[lastIdx],
                      citations: event.citations,
                      retrieval_latency_ms: event.retrieval_latency_ms,
                    };
                  }
                  return updated;
                });
              } else if (event.type === "token") {
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  if (lastIdx >= 0 && updated[lastIdx].role === "assistant") {
                    updated[lastIdx] = {
                      ...updated[lastIdx],
                      content: updated[lastIdx].content + event.content,
                    };
                  }
                  return updated;
                });
              } else if (event.type === "done") {
                setActiveAgentStatus(null);
              }
            } catch (e) {
              console.error("Error parsing SSE event", e);
            }
          }
        }
      }
    } catch (err: any) {
      console.error("Chat streaming error", err);
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last && last.role === "assistant") {
          last.content += `\n\n*(Error during generation: ${err?.message || "connection error"})*`;
        }
        return updated;
      });
    } finally {
      setIsStreaming(false);
      setActiveAgentStatus(null);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#090d16] text-slate-100 overflow-hidden font-sans">
      {/* Top Navbar */}
      <Navbar
        currentRepo={currentRepo}
        onOpenConnectModal={() => setIsConnectModalOpen(true)}
        onOpenEvalModal={() => setIsEvalModalOpen(true)}
        onOpenSettingsModal={() => setIsSettingsModalOpen(true)}
        onRefreshIndex={handleRefreshIndex}
        isIndexing={currentRepo?.status !== "COMPLETED" && currentRepo?.status !== "FAILED"}
      />

      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <aside className="w-64 border-r border-slate-800 bg-[#0d1322] flex flex-col shrink-0 select-none">
          {/* Repository Selector */}
          <div className="p-3 border-b border-slate-800">
            <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Active Repository
            </label>
            <select
              value={currentRepo?.id || ""}
              onChange={(e) => {
                const r = repositories.find((x) => x.id === e.target.value);
                if (r) handleSelectRepository(r);
              }}
              className="w-full text-xs bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-blue-500"
            >
              {repositories.map((repo) => (
                <option key={repo.id} value={repo.id}>
                  {repo.full_name}
                </option>
              ))}
            </select>
          </div>

          {/* Indexing Progress Bar */}
          {currentRepo && currentRepo.status !== "COMPLETED" && (
            <div className="p-3 border-b border-slate-800 bg-blue-950/20">
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="font-semibold text-blue-400">{currentRepo.status}</span>
                <span className="text-slate-400">{currentRepo.progress_percentage || 0}%</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-blue-500 h-full transition-all duration-300"
                  style={{ width: `${currentRepo.progress_percentage || 10}%` }}
                />
              </div>
              <p className="text-[10px] text-slate-400 mt-1 truncate">
                {currentRepo.status_message || "Processing..."}
              </p>
            </div>
          )}

          {/* File Explorer Tree */}
          <div className="flex-1 overflow-y-auto p-2">
            <div className="flex items-center justify-between px-2 py-1 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              <div className="flex items-center space-x-1.5">
                <FolderTree className="w-3.5 h-3.5 text-slate-400" />
                <span>Files ({currentRepo?.total_files || 0})</span>
              </div>
            </div>
            <FileTree
              nodes={fileTree}
              onSelectFile={(path) => handleOpenFile(path, null)}
              selectedFilePath={activeFilePath}
            />
          </div>

          {/* Specialized Agents Roster */}
          <div className="p-3 border-t border-slate-800 bg-slate-900/40">
            <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
              LangGraph Specialized Agents
            </label>
            <div className="grid grid-cols-2 gap-1 text-[10px]">
              <div className="flex items-center space-x-1.5 p-1 rounded bg-slate-800/40 text-slate-300">
                <Bug className="w-3 h-3 text-red-400" />
                <span>Debug Agent</span>
              </div>
              <div className="flex items-center space-x-1.5 p-1 rounded bg-slate-800/40 text-slate-300">
                <Shield className="w-3 h-3 text-emerald-400" />
                <span>Security</span>
              </div>
              <div className="flex items-center space-x-1.5 p-1 rounded bg-slate-800/40 text-slate-300">
                <Cpu className="w-3 h-3 text-purple-400" />
                <span>Architecture</span>
              </div>
              <div className="flex items-center space-x-1.5 p-1 rounded bg-slate-800/40 text-slate-300">
                <Terminal className="w-3 h-3 text-cyan-400" />
                <span>DevOps</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Center Chat Workspace */}
        <main className="flex-1 flex flex-col min-w-0 bg-[#090d16] relative">
          {/* Chat Messages Scrollable Area */}
          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-5">
            {messages.length === 0 ? (
              <div className="max-w-2xl mx-auto my-auto pt-10 text-center space-y-6">
                <div className="inline-flex p-3 rounded-2xl bg-gradient-to-tr from-blue-600/20 via-indigo-600/20 to-cyan-500/20 border border-blue-500/30 shadow-xl shadow-blue-500/10">
                  <Sparkles className="w-8 h-8 text-blue-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-100">
                    Welcome to RepoPilot Engineering Copilot
                  </h2>
                  <p className="text-xs text-slate-400 mt-1 max-w-lg mx-auto">
                    Ask questions, diagnose errors, investigate security vulnerabilities, and receive answers strictly grounded in repository source code with clickable line citations.
                  </p>
                </div>

                {/* Quick Query Starters */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-left pt-2">
                  {[
                    "Why is the login endpoint returning 401?",
                    "Explain the architecture of this repository.",
                    "Where is authentication implemented?",
                    "Why is Docker deployment failing?",
                    "Find potential security vulnerabilities.",
                    "Find all places where JWT tokens are validated.",
                  ].map((starter, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(starter)}
                      className="p-3 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-blue-500/50 text-xs text-slate-300 hover:text-slate-100 transition-all flex items-center justify-between group shadow-sm"
                    >
                      <span className="truncate pr-2 font-medium">{starter}</span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-blue-400 transition-transform group-hover:translate-x-0.5 shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex flex-col ${
                    msg.role === "user" ? "items-end" : "items-start"
                  }`}
                >
                  <div
                    className={`max-w-3xl rounded-2xl p-4 text-xs ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white shadow-md shadow-blue-600/20"
                        : "bg-[#0e1628] border border-slate-800 text-slate-200 shadow-xl w-full"
                    }`}
                  >
                    {/* Header info */}
                    <div className="flex items-center space-x-2 mb-2 pb-1.5 border-b border-white/10">
                      {msg.role === "user" ? (
                        <>
                          <User className="w-3.5 h-3.5" />
                          <span className="font-semibold text-[11px]">Developer</span>
                        </>
                      ) : (
                        <>
                          <Bot className="w-3.5 h-3.5 text-blue-400" />
                          <span className="font-semibold text-[11px] text-blue-400">
                            {msg.agent_name || "RepoPilot Copilot"}
                          </span>
                          {msg.retrieval_latency_ms && (
                            <span className="text-[10px] text-slate-400 font-mono">
                              • Retrieved in {msg.retrieval_latency_ms}ms
                            </span>
                          )}
                        </>
                      )}
                    </div>

                    {/* Markdown Message Content */}
                    <div className="markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>

                    {/* Grounded Source Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-2.5 border-t border-slate-800/80">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1.5">
                          Evidence Citations (Click to view lines in Monaco):
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.citations.map((c, cIdx) => (
                            <button
                              key={cIdx}
                              onClick={() =>
                                handleOpenFile(c.file_path, {
                                  startLine: c.start_line,
                                  endLine: c.end_line,
                                })
                              }
                              className="inline-flex items-center space-x-1.5 px-2 py-1 rounded bg-slate-800/80 hover:bg-blue-600/20 border border-slate-700 hover:border-blue-500/50 text-[11px] font-mono text-cyan-300 hover:text-cyan-200 transition-colors cursor-pointer"
                            >
                              <FileCode className="w-3 h-3 text-cyan-400" />
                              <span>
                                {c.file_path}:{c.start_line}-{c.end_line}
                              </span>
                              <ExternalLink className="w-2.5 h-2.5 text-slate-500" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}

            {/* Active Streaming Agent Status Indicator */}
            {activeAgentStatus && (
              <div className="flex items-center space-x-2 text-xs text-blue-400 bg-blue-500/10 border border-blue-500/20 px-3 py-1.5 rounded-lg max-w-sm animate-pulse">
                <span className="w-2 h-2 rounded-full bg-blue-400" />
                <span>{activeAgentStatus}</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Bottom Chat Input Bar */}
          <div className="p-3 border-t border-slate-800 bg-[#0d1322]">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="max-w-4xl mx-auto flex items-center space-x-2"
            >
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  disabled={isStreaming || !currentRepo}
                  placeholder={
                    currentRepo
                      ? "Ask RepoPilot anything about this repository (e.g. 'Why is login returning 401?')..."
                      : "Please connect or select a repository first..."
                  }
                  className="w-full text-xs bg-slate-900/90 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 shadow-inner"
                />
              </div>

              <button
                type="submit"
                disabled={isStreaming || !inputQuery.trim() || !currentRepo}
                className="px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-40 text-white rounded-xl shadow-lg shadow-blue-600/20 transition-all shrink-0 flex items-center justify-center"
              >
                <Send className="w-4 h-4" />
              </button>

              {messages.length > 0 && (
                <button
                  type="button"
                  onClick={() => setMessages([])}
                  title="Clear conversation"
                  className="p-3 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors shrink-0"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </form>
          </div>
        </main>

        {/* Right Monaco Code Viewer Panel */}
        {isCodeViewerOpen && activeFilePath && (
          <aside className="w-1/2 shrink-0 h-full border-l border-slate-800 flex flex-col z-20 shadow-2xl animate-in slide-in-from-right duration-200">
            <CodeViewer
              filePath={activeFilePath}
              content={activeFileContent}
              highlightRange={highlightRange}
              onClose={() => setIsCodeViewerOpen(false)}
            />
          </aside>
        )}
      </div>

      {/* Modals */}
      <ConnectRepoModal
        isOpen={isConnectModalOpen}
        onClose={() => setIsConnectModalOpen(false)}
        onConnect={handleConnectRepo}
        isLoading={isConnecting}
      />

      <EvaluationModal
        isOpen={isEvalModalOpen}
        onClose={() => setIsEvalModalOpen(false)}
        repositoryId={currentRepo?.id}
      />

      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
      />
    </div>
  );
}
