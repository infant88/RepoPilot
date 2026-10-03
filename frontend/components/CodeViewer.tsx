"use client";

import React, { useRef, useEffect } from "react";
import Editor, { Monaco } from "@monaco-editor/react";
import { X, ExternalLink, Code2, Copy, Check } from "lucide-react";

interface CodeViewerProps {
  filePath: string;
  content: string;
  language?: string | null;
  highlightRange?: { startLine: number; endLine: number } | null;
  onClose: () => void;
}

export default function CodeViewer({
  filePath,
  content,
  language,
  highlightRange,
  onClose,
}: CodeViewerProps) {
  const editorRef = useRef<any>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const decorationsRef = useRef<any[]>([]);
  const [copied, setCopied] = React.useState(false);

  // Map file extension to Monaco language mode
  const getMonacoLanguage = (path: string, lang?: string | null) => {
    if (lang) {
      if (lang === "python") return "python";
      if (lang === "typescript") return "typescript";
      if (lang === "javascript") return "javascript";
      if (lang === "markdown") return "markdown";
      if (lang === "yaml") return "yaml";
      if (lang === "json") return "json";
      if (lang === "dockerfile") return "dockerfile";
    }
    const lower = path.toLowerCase();
    if (lower.endsWith(".py")) return "python";
    if (lower.endsWith(".ts") || lower.endsWith(".tsx")) return "typescript";
    if (lower.endsWith(".js") || lower.endsWith(".jsx")) return "javascript";
    if (lower.endsWith(".json")) return "json";
    if (lower.endsWith(".yml") || lower.endsWith(".yaml")) return "yaml";
    if (lower.endsWith(".md")) return "markdown";
    if (lower.includes("dockerfile")) return "dockerfile";
    return "plaintext";
  };

  const handleEditorDidMount = (editor: any, monaco: Monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    applyHighlight();
  };

  const applyHighlight = () => {
    if (!editorRef.current || !monacoRef.current || !highlightRange) return;

    const editor = editorRef.current;
    const monaco = monacoRef.current;
    const { startLine, endLine } = highlightRange;

    // Clear previous decorations
    decorationsRef.current = editor.deltaDecorations(decorationsRef.current, []);

    // Add new highlight decoration
    decorationsRef.current = editor.deltaDecorations(
      [],
      [
        {
          range: new monaco.Range(startLine, 1, endLine, 1),
          options: {
            isWholeLine: true,
            className: "bg-blue-600/20 border-l-4 border-blue-500",
            linesDecorationsClassName: "bg-blue-500",
          },
        },
      ]
    );

    // Scroll to highlighted line
    editor.revealLineInCenter(startLine);
  };

  useEffect(() => {
    applyHighlight();
  }, [highlightRange, content]);

  const copyCode = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="h-full flex flex-col bg-[#0b101d] border-l border-slate-800">
      {/* Code Header */}
      <div className="h-10 px-4 flex items-center justify-between border-b border-slate-800 bg-[#0f172a]/70">
        <div className="flex items-center space-x-2 truncate">
          <Code2 className="w-4 h-4 text-blue-400 shrink-0" />
          <span className="text-xs font-mono font-medium text-slate-200 truncate">
            {filePath}
          </span>
          {highlightRange && (
            <span className="text-[10px] font-mono px-1.5 py-0.2 bg-blue-500/10 text-blue-400 rounded border border-blue-500/20 shrink-0">
              L{highlightRange.startLine}-{highlightRange.endLine}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={copyCode}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="Copy code"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="Close code viewer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Monaco Editor Container */}
      <div className="flex-1 w-full relative">
        <Editor
          height="100%"
          path={filePath}
          defaultLanguage={getMonacoLanguage(filePath, language)}
          language={getMonacoLanguage(filePath, language)}
          value={content}
          theme="vs-dark"
          options={{
            readOnly: true,
            minimap: { enabled: true },
            fontSize: 13,
            lineNumbers: "on",
            renderLineHighlight: "all",
            scrollBeyondLastLine: false,
            wordWrap: "on",
            automaticLayout: true,
            padding: { top: 12 },
          }}
          onMount={handleEditorDidMount}
        />
      </div>
    </div>
  );
}
