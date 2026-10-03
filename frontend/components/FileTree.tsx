"use client";

import React, { useState } from "react";
import { Folder, FolderOpen, FileCode, FileText, ChevronRight, ChevronDown } from "lucide-react";

export interface FileTreeNode {
  name: string;
  path: string;
  type: "file" | "directory";
  language?: string | null;
  children?: FileTreeNode[] | null;
}

interface FileTreeProps {
  nodes: FileTreeNode[];
  onSelectFile: (path: string) => void;
  selectedFilePath: string | null;
}

export default function FileTree({ nodes, onSelectFile, selectedFilePath }: FileTreeProps) {
  if (!nodes || nodes.length === 0) {
    return (
      <div className="p-4 text-xs text-slate-500 italic text-center">
        No files indexed yet.
      </div>
    );
  }

  return (
    <div className="text-xs select-none space-y-0.5">
      {nodes.map((node) => (
        <FileTreeItem
          key={node.path}
          node={node}
          onSelectFile={onSelectFile}
          selectedFilePath={selectedFilePath}
          depth={0}
        />
      ))}
    </div>
  );
}

function FileTreeItem({
  node,
  onSelectFile,
  selectedFilePath,
  depth,
}: {
  node: FileTreeNode;
  onSelectFile: (path: string) => void;
  selectedFilePath: string | null;
  depth: number;
}) {
  const [isOpen, setIsOpen] = useState(true);
  const isSelected = selectedFilePath === node.path;
  const isDirectory = node.type === "directory";

  const handleClick = () => {
    if (isDirectory) {
      setIsOpen(!isOpen);
    } else {
      onSelectFile(node.path);
    }
  };

  const getFileIcon = (fileName: string, lang?: string | null) => {
    if (fileName.endsWith(".py") || fileName.endsWith(".ts") || fileName.endsWith(".js")) {
      return <FileCode className="w-3.5 h-3.5 text-blue-400 shrink-0" />;
    }
    if (fileName.endsWith(".md") || fileName.endsWith(".txt")) {
      return <FileText className="w-3.5 h-3.5 text-amber-400 shrink-0" />;
    }
    return <FileCode className="w-3.5 h-3.5 text-slate-400 shrink-0" />;
  };

  return (
    <div>
      <div
        onClick={handleClick}
        style={{ paddingLeft: `${depth * 12 + 6}px` }}
        className={`flex items-center space-x-1.5 py-1 pr-2 rounded cursor-pointer transition-colors ${
          isSelected
            ? "bg-blue-600/20 text-blue-400 font-medium border-l-2 border-blue-500"
            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
        }`}
      >
        {isDirectory ? (
          <>
            {isOpen ? (
              <ChevronDown className="w-3 h-3 text-slate-500 shrink-0" />
            ) : (
              <ChevronRight className="w-3 h-3 text-slate-500 shrink-0" />
            )}
            {isOpen ? (
              <FolderOpen className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            ) : (
              <Folder className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            )}
          </>
        ) : (
          <>
            <span className="w-3" />
            {getFileIcon(node.name, node.language)}
          </>
        )}
        <span className="truncate">{node.name}</span>
      </div>

      {isDirectory && isOpen && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeItem
              key={child.path}
              node={child}
              onSelectFile={onSelectFile}
              selectedFilePath={selectedFilePath}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}
