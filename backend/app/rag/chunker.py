import ast
import hashlib
import re
from typing import List, Dict, Any, Optional

class RawChunk:
    def __init__(
        self,
        content: str,
        start_line: int,
        end_line: int,
        symbol_name: Optional[str] = None,
        symbol_type: Optional[str] = None,
        chunk_type: str = "code",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.content = content.strip()
        self.start_line = start_line
        self.end_line = end_line
        self.symbol_name = symbol_name
        self.symbol_type = symbol_type
        self.chunk_type = chunk_type
        self.metadata = metadata or {}
        self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()

class BaseLanguageParser:
    def parse(self, code: str, file_path: str) -> List[RawChunk]:
        raise NotImplementedError

class PythonParser(BaseLanguageParser):
    def parse(self, code: str, file_path: str) -> List[RawChunk]:
        chunks: List[RawChunk] = []
        lines = code.splitlines()
        total_lines = len(lines)
        if not lines:
            return chunks

        try:
            tree = ast.parse(code)
            covered_lines = set()

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start = node.lineno
                    end = getattr(node, "end_lineno", start + len(node.body))
                    chunk_content = "\n".join(lines[start - 1 : end])
                    chunks.append(
                        RawChunk(
                            content=chunk_content,
                            start_line=start,
                            end_line=end,
                            symbol_name=node.name,
                            symbol_type="function",
                            chunk_type="code",
                            metadata={"is_async": isinstance(node, ast.AsyncFunctionDef)},
                        )
                    )
                    covered_lines.update(range(start, end + 1))

                elif isinstance(node, ast.ClassDef):
                    start = node.lineno
                    end = getattr(node, "end_lineno", start + len(node.body))
                    class_content = "\n".join(lines[start - 1 : end])
                    
                    # Add class header / overview chunk
                    chunks.append(
                        RawChunk(
                            content=class_content,
                            start_line=start,
                            end_line=end,
                            symbol_name=node.name,
                            symbol_type="class",
                            chunk_type="code",
                            metadata={"docstring": ast.get_docstring(node)},
                        )
                    )
                    covered_lines.update(range(start, end + 1))

                    # Also extract methods inside class for fine-grained retrieval
                    for subnode in node.body:
                        if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            m_start = subnode.lineno
                            m_end = getattr(subnode, "end_lineno", m_start + len(subnode.body))
                            m_content = "\n".join(lines[m_start - 1 : m_end])
                            chunks.append(
                                RawChunk(
                                    content=m_content,
                                    start_line=m_start,
                                    end_line=m_end,
                                    symbol_name=f"{node.name}.{subnode.name}",
                                    symbol_type="method",
                                    chunk_type="code",
                                    metadata={"parent_class": node.name},
                                )
                            )

            # If there is top-level module code (imports, constants, config) not inside classes/functions
            uncovered_starts = [i for i in range(1, total_lines + 1) if i not in covered_lines and lines[i-1].strip()]
            if uncovered_starts:
                # Group contiguous top-level lines into module chunks
                cur_block: List[int] = []
                for line_num in range(1, total_lines + 1):
                    if line_num not in covered_lines and lines[line_num - 1].strip():
                        cur_block.append(line_num)
                    else:
                        if cur_block:
                            s = cur_block[0]
                            e = cur_block[-1]
                            cnt = "\n".join(lines[s - 1 : e])
                            if len(cnt.strip()) > 20:
                                chunks.append(
                                    RawChunk(
                                        content=cnt,
                                        start_line=s,
                                        end_line=e,
                                        symbol_name="module_scope",
                                        symbol_type="module",
                                        chunk_type="code",
                                    )
                                )
                            cur_block = []
                if cur_block:
                    s = cur_block[0]
                    e = cur_block[-1]
                    cnt = "\n".join(lines[s - 1 : e])
                    if len(cnt.strip()) > 20:
                        chunks.append(
                            RawChunk(
                                content=cnt,
                                start_line=s,
                                end_line=e,
                                symbol_name="module_scope",
                                symbol_type="module",
                                chunk_type="code",
                            )
                        )

        except Exception:
            # Fallback if Python AST parsing fails (e.g. syntax error in repo file)
            return GenericLineChunker().chunk(code)

        return sorted(chunks, key=lambda c: c.start_line) if chunks else GenericLineChunker().chunk(code)

class BraceLanguageParser(BaseLanguageParser):
    """Parser for C-style languages (JS/TS, Java, C++, Go, Rust) with block recognition."""
    def __init__(self, language: str):
        self.language = language

    def parse(self, code: str, file_path: str) -> List[RawChunk]:
        chunks: List[RawChunk] = []
        lines = code.splitlines()
        if not lines:
            return chunks

        # Regex patterns for symbols
        patterns = [
            (r'^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)', 'function'),
            (r'^\s*(?:export\s+)?(?:abstract\s+)?class\s+([a-zA-Z0-9_$]+)', 'class'),
            (r'^\s*(?:export\s+)?interface\s+([a-zA-Z0-9_$]+)', 'interface'),
            (r'^\s*(?:export\s+)?type\s+([a-zA-Z0-9_$]+)', 'type'),
            (r'^\s*(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>', 'function'),
            (r'^\s*func\s+(?:\([^)]+\)\s+)?([a-zA-Z0-9_]+)\s*\(', 'function'), # Go
            (r'^\s*fn\s+([a-zA-Z0-9_]+)\s*\(', 'function'), # Rust
            (r'^\s*struct\s+([a-zA-Z0-9_]+)', 'struct'),
            (r'^\s*impl(?:\s+[a-zA-Z0-9_]+)?\s+for\s+([a-zA-Z0-9_]+)', 'impl'),
            (r'^\s*(?:public|private|protected)?\s*(?:static)?\s*[\w\<\>\[\]]+\s+([a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{', 'method'),
        ]

        total_lines = len(lines)
        i = 0
        while i < total_lines:
            line = lines[i]
            matched = False
            for pat, sym_type in patterns:
                m = re.search(pat, line)
                if m:
                    sym_name = m.group(1)
                    start_line = i + 1
                    # Find matching brace
                    brace_count = line.count("{") - line.count("}")
                    end_line = start_line
                    j = i + 1
                    while j < total_lines:
                        brace_count += lines[j].count("{") - lines[j].count("}")
                        if brace_count <= 0 and "{" in "".join(lines[i : j + 1]):
                            end_line = j + 1
                            break
                        j += 1
                    else:
                        end_line = min(start_line + 40, total_lines)

                    chunk_code = "\n".join(lines[start_line - 1 : end_line])
                    chunks.append(
                        RawChunk(
                            content=chunk_code,
                            start_line=start_line,
                            end_line=end_line,
                            symbol_name=sym_name,
                            symbol_type=sym_type,
                            chunk_type="code",
                        )
                    )
                    i = max(i + 1, end_line)
                    matched = True
                    break
            if not matched:
                i += 1

        if not chunks:
            return GenericLineChunker().chunk(code)
        return chunks

class MarkdownParser(BaseLanguageParser):
    def parse(self, code: str, file_path: str) -> List[RawChunk]:
        chunks: List[RawChunk] = []
        lines = code.splitlines()
        if not lines:
            return chunks

        heading_indices = []
        for idx, line in enumerate(lines):
            if re.match(r"^#{1,4}\s+", line):
                heading_indices.append(idx)

        if not heading_indices:
            return GenericLineChunker().chunk(code, chunk_type="documentation")

        for idx, start_idx in enumerate(heading_indices):
            end_idx = heading_indices[idx + 1] if idx + 1 < len(heading_indices) else len(lines)
            section_content = "\n".join(lines[start_idx:end_idx]).strip()
            heading_title = lines[start_idx].lstrip("#").strip()
            if section_content:
                chunks.append(
                    RawChunk(
                        content=section_content,
                        start_line=start_idx + 1,
                        end_line=end_idx,
                        symbol_name=heading_title,
                        symbol_type="section",
                        chunk_type="documentation",
                    )
                )
        return chunks

class GenericLineChunker:
    """Sliding-window line chunker that respects line boundaries and max chunk sizes."""
    def __init__(self, max_lines: int = 50, overlap_lines: int = 5):
        self.max_lines = max_lines
        self.overlap_lines = overlap_lines

    def chunk(self, code: str, chunk_type: str = "code") -> List[RawChunk]:
        chunks: List[RawChunk] = []
        lines = code.splitlines()
        total = len(lines)
        if total == 0:
            return chunks

        step = max(1, self.max_lines - self.overlap_lines)
        for i in range(0, total, step):
            start = i + 1
            end = min(i + self.max_lines, total)
            chunk_content = "\n".join(lines[i:end]).strip()
            if chunk_content:
                chunks.append(
                    RawChunk(
                        content=chunk_content,
                        start_line=start,
                        end_line=end,
                        symbol_name=None,
                        symbol_type=None,
                        chunk_type=chunk_type,
                    )
                )
            if end >= total:
                break
        return chunks

class CodeAwareChunker:
    """Master chunker dispatching to language-specific parsers."""
    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".md": "markdown",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".json": "json",
        ".sh": "shell",
        "dockerfile": "dockerfile",
    }

    def __init__(self):
        self.python_parser = PythonParser()
        self.markdown_parser = MarkdownParser()
        self.brace_parser = BraceLanguageParser("generic")
        self.generic_chunker = GenericLineChunker()

    def detect_language(self, file_path: str) -> str:
        lower = file_path.lower()
        if "dockerfile" in lower:
            return "dockerfile"
        for ext, lang in self.LANGUAGE_EXTENSIONS.items():
            if lower.endswith(ext):
                return lang
        return "text"

    def chunk_file(self, content: str, file_path: str) -> List[RawChunk]:
        lang = self.detect_language(file_path)
        if lang == "python":
            return self.python_parser.parse(content, file_path)
        elif lang in ("javascript", "typescript", "go", "rust", "java", "cpp", "c"):
            return self.brace_parser.parse(content, file_path)
        elif lang == "markdown":
            return self.markdown_parser.parse(content, file_path)
        elif lang in ("yaml", "json", "dockerfile", "shell"):
            return self.generic_chunker.chunk(content, chunk_type="config")
        else:
            return self.generic_chunker.chunk(content, chunk_type="text")
