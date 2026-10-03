import re
from typing import List, Dict, Any, Optional

class QueryAnalysis:
    def __init__(
        self,
        original_query: str,
        intent: str, # debug, security, architecture, devops, code, documentation, general
        rewritten_queries: List[str],
        likely_languages: List[str],
        likely_file_patterns: List[str],
        is_debugging: bool = False,
        is_security: bool = False,
        is_architecture: bool = False,
        is_devops: bool = False,
    ):
        self.original_query = original_query
        self.intent = intent
        self.rewritten_queries = rewritten_queries
        self.likely_languages = likely_languages
        self.likely_file_patterns = likely_file_patterns
        self.is_debugging = is_debugging
        self.is_security = is_security
        self.is_architecture = is_architecture
        self.is_devops = is_devops

class QueryUnderstandingEngine:
    """
    Analyzes developer queries, determines task intent, detects key technologies,
    and produces high-relevance search query rewrites.
    """
    def analyze(self, query: str) -> QueryAnalysis:
        q_lower = query.lower()
        rewritten: List[str] = [query]

        # 1. Intent Detection
        is_debugging = any(w in q_lower for w in ["why", "error", "fail", "401", "403", "404", "500", "broken", "bug", "crash", "fix", "exception", "traceback"])
        is_security = any(w in q_lower for w in ["security", "vulnerability", "secret", "token", "cve", "injection", "sanitize", "jwt", "permission", "cors", "leak"])
        is_architecture = any(w in q_lower for w in ["architecture", "flow", "structure", "design", "overview", "service", "dependency", "how does", "system"])
        is_devops = any(w in q_lower for w in ["docker", "dockerfile", "compose", "deploy", "kubernetes", "k8s", "ci", "github actions", "pipeline", "env", "environment"])
        is_docs = any(w in q_lower for w in ["readme", "document", "docs", "setup", "install", "how to run"])

        if is_debugging:
            intent = "debug"
        elif is_security:
            intent = "security"
        elif is_devops:
            intent = "devops"
        elif is_architecture:
            intent = "architecture"
        elif is_docs:
            intent = "documentation"
        else:
            intent = "code"

        # 2. Query Rewriting for Search Expansion
        # Authentication & 401 scenarios
        if "401" in q_lower or "unauthorized" in q_lower or "login" in q_lower:
            rewritten.extend([
                "authenticate_user verify_jwt_token",
                "AuthenticationMiddleware bearer authorization",
                "JWT_SECRET settings config",
                "HTTP_401_UNAUTHORIZED login",
            ])

        # Docker / Deployment failure
        if "docker" in q_lower or "deployment" in q_lower:
            rewritten.extend([
                "docker-compose environment variables",
                "Dockerfile CMD ENTRYPOINT",
                "settings environment config",
            ])

        # Security check
        if is_security:
            rewritten.extend([
                "verify_token secret password",
                "CORS allow_origins",
                "credentials environment",
            ])

        # 3. Detect likely file patterns
        patterns: List[str] = []
        if "auth" in q_lower or "login" in q_lower:
            patterns.extend(["auth", "middleware", "jwt", "user"])
        if "docker" in q_lower:
            patterns.extend(["docker", "compose", "config", "env"])
        if "route" in q_lower or "api" in q_lower:
            patterns.extend(["route", "api", "controller", "endpoint"])

        # 4. Detect likely languages
        langs: List[str] = []
        if any(w in q_lower for w in ["python", "fastapi", "django", "flask", "py"]):
            langs.append("python")
        if any(w in q_lower for w in ["typescript", "ts", "next.js", "react"]):
            langs.append("typescript")
        if any(w in q_lower for w in ["javascript", "js", "node"]):
            langs.append("javascript")

        return QueryAnalysis(
            original_query=query,
            intent=intent,
            rewritten_queries=list(dict.fromkeys(rewritten)), # Deduplicate
            likely_languages=langs,
            likely_file_patterns=patterns,
            is_debugging=is_debugging,
            is_security=is_security,
            is_architecture=is_architecture,
            is_devops=is_devops,
        )

query_understanding_engine = QueryUnderstandingEngine()
