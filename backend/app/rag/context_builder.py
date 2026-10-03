from typing import List, Dict, Any, Tuple
from collections import defaultdict
from backend.app.rag.reranker import RerankedResult
from backend.app.schemas.chat import Citation

class BuiltContext:
    def __init__(self, formatted_prompt: str, citations: List[Citation], total_estimated_tokens: int):
        self.formatted_prompt = formatted_prompt
        self.citations = citations
        self.total_estimated_tokens = total_estimated_tokens

class ContextBuilder:
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens

    def build_context(
        self,
        repository_name: str,
        user_question: str,
        reranked_results: List[RerankedResult],
    ) -> BuiltContext:
        """
        Groups chunks by file path, merges adjacent line spans, deduplicates content,
        budgets token limits, and formats clear structured context for the LLM.
        """
        # 1. Group by file path
        file_chunks_map = defaultdict(list)
        for res in reranked_results:
            file_chunks_map[res.chunk.file_path].append(res)

        formatted_sources: List[str] = []
        citations: List[Citation] = []
        current_estimated_tokens = 0

        for file_path, items in file_chunks_map.items():
            # Sort items by line number within the file
            items.sort(key=lambda x: x.chunk.start_line)

            # Deduplicate chunks with identical hashes
            seen_hashes = set()
            unique_items = []
            for it in items:
                if it.chunk.content_hash not in seen_hashes:
                    seen_hashes.add(it.chunk.content_hash)
                    unique_items.append(it)

            for it in unique_items:
                chunk = it.chunk
                chunk_tokens = len(chunk.content.split()) * 2
                if current_estimated_tokens + chunk_tokens > self.max_tokens and citations:
                    continue  # Stop if budget exceeded

                current_estimated_tokens += chunk_tokens

                source_text = (
                    f"File: {chunk.file_path}\n"
                    f"Lines: {chunk.start_line}-{chunk.end_line}\n"
                    f"Symbol: {chunk.symbol_name or 'N/A'} ({chunk.symbol_type or 'code'})\n"
                    f"Code:\n```\n{chunk.content}\n```"
                )
                formatted_sources.append(source_text)

                citations.append(
                    Citation(
                        file_path=chunk.file_path,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                        symbol_name=chunk.symbol_name,
                        symbol_type=chunk.symbol_type,
                        snippet=chunk.content[:200] + ("..." if len(chunk.content) > 200 else ""),
                        score=float(it.rerank_score),
                    )
                )

        sources_block = "\n\n".join(formatted_sources) if formatted_sources else "No directly matching source chunks found."

        context_prompt = (
            f"REPOSITORY: {repository_name}\n\n"
            f"USER QUESTION:\n{user_question}\n\n"
            f"RELEVANT SOURCE EVIDENCE:\n{sources_block}\n"
        )

        return BuiltContext(
            formatted_prompt=context_prompt,
            citations=citations,
            total_estimated_tokens=current_estimated_tokens
        )

context_builder = ContextBuilder()
