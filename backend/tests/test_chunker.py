import pytest
from backend.app.rag.chunker import CodeAwareChunker, PythonParser

def test_python_ast_chunker():
    sample_code = """
import os

def authenticate_user(username: str, password: str):
    \"\"\"Authenticate user docstring.\"\"\"
    if username == "admin":
        return True
    return False

class AuthManager:
    def __init__(self, secret: str):
        self.secret = secret

    def verify_token(self, token: str):
        return token == self.secret
"""
    parser = PythonParser()
    chunks = parser.parse(sample_code, "test_auth.py")
    
    assert len(chunks) >= 3
    symbols = [c.symbol_name for c in chunks]
    assert "authenticate_user" in symbols
    assert "AuthManager" in symbols
    assert any("verify_token" in s for s in symbols if s)
    
    # Verify line numbers
    auth_chunk = next(c for c in chunks if c.symbol_name == "authenticate_user")
    assert auth_chunk.start_line == 4
    assert auth_chunk.end_line >= 8
    assert "return True" in auth_chunk.content

def test_language_detection():
    chunker = CodeAwareChunker()
    assert chunker.detect_language("app/main.py") == "python"
    assert chunker.detect_language("src/index.ts") == "typescript"
    assert chunker.detect_language("src/Component.jsx") == "javascript"
    assert chunker.detect_language("Dockerfile") == "dockerfile"
    assert chunker.detect_language("docs/README.md") == "markdown"
    assert chunker.detect_language("config.yaml") == "yaml"
