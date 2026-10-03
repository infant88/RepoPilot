# RepoPilot Architecture & Technical Specification

## Overview
RepoPilot is designed as an AI Engineering Copilot that delivers grounded, citation-backed answers to developers navigating large codebases.

## 1. Hybrid Retrieval & Reranking Architecture

```
User Query
    │
    ▼
Query Understanding Engine
    ├─ Intent Detection: debug | security | architecture | devops | code | docs
    └─ Query Rewriter (produces expanded technical tokens)
    │
    ├──► 1. Dense Semantic Vector Search (pgvector cosine similarity) -> Top 20 Candidates
    │
    └──► 2. Sparse Lexical Search (BM25Okapi over code tokens)        -> Top 20 Candidates
            │
            ▼
    Reciprocal Rank Fusion (RRF):
    RRF_score(d) = sum_{m in models} [ w_m / (60 + rank_m(d)) ]
            │
            ▼
    Merged Candidate Pool (Top 35 Candidates)
            │
            ▼
    Multi-Factor Cross-Encoder Reranker:
    - Symbol match boost (+0.35 for function/class name overlap)
    - Path relevance boost (+0.20 for module matches)
    - HTTP status / error boost (+0.40 for 401, 500, etc.)
    - Token overlap density (+0.30)
            │
            ▼
    Top 8 Highly Relevant Chunks
            │
            ▼
    Context Builder (Groups by file, merges contiguous lines, enforces token budget)
            │
            ▼
    Grounded Response Generator (SSE streaming + line citations)
```

## 2. Specialized LangGraph Agents

The router evaluates incoming queries and delegates them to one of six specialized agents:
- **Debug Agent**: Traces stack traces, 401/403/500 HTTP errors, and token verification paths.
- **Security Agent**: Identifies secret leaks, fallback keys, and unauthenticated endpoints.
- **Architecture Agent**: Understands modules, data layer interactions, and dependencies.
- **DevOps Agent**: Inspects Dockerfile recipes, compose variable injection, and CI configs.
- **Code Agent**: Explains function signatures, type contracts, and algorithms.
- **Documentation Agent**: Generates README guides and API summaries.

## 3. Database Schema

- `repositories`: Metadata, GitHub URL, default branch, status, indexing progress, language breakdown.
- `repository_files`: File paths, content hashes (SHA-256), languages, file sizes, and raw text.
- `code_chunks`: Logical AST blocks, start_line, end_line, symbol_name, symbol_type, content, and 384-dim vector embeddings.
- `conversations` & `messages`: Multi-turn chat history with citation metadata and latency tracking.
- `agent_runs`: Intermediate execution steps and tool invocations.
- `evaluation_datasets` & `evaluation_results`: Precision, Recall, Faithfulness, Relevance, and latency benchmarks.
