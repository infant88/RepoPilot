from typing import Optional, Dict, Any
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.responses import JSONResponse
from backend.config.settings import settings
from backend.auth.jwt import verify_jwt_token

def authenticate_user(username: str, password_plain: str) -> Optional[Dict[str, Any]]:
    """
    Validates user credentials against stored account database.
    Returns user dict on success, None on invalid credentials.
    """
    # Demo mock database record
    MOCK_USERS = {
        "admin@example.com": {"id": 101, "password": "password123", "role": "admin"},
        "developer@example.com": {"id": 102, "password": "devpassword", "role": "engineer"},
    }
    user = MOCK_USERS.get(username)
    if not user or user["password"] != password_plain:
        return None
    return {"id": user["id"], "username": username, "role": user["role"]}

class AuthenticationMiddleware:
    """
    ASGI Middleware that validates incoming Bearer tokens.
    Extracts Bearer token from Authorization header and verifies with settings.JWT_SECRET.
    """
    def __init__(self, app: ASGIApp):
        self.app = app
        self.exempt_paths = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/docs",
            "/openapi.json",
            "/health",
        }

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in self.exempt_paths:
            await self.app(scope, receive, send)
            return

        # Extract Authorization header
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode("utf-8")

        if not auth_header or not auth_header.startswith("Bearer "):
            response = JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid authorization header. Must be Bearer token."}
            )
            await response(scope, receive, send)
            return

        token = auth_header.split(" ", 1)[1].strip()
        try:
            # Validates token using configured secret
            # Common Root Cause: In Docker deployments, JWT_SECRET might not be populated in environment variables
            payload = verify_jwt_token(token, secret=settings.JWT_SECRET)
            scope["user"] = payload
        except Exception as err:
            response = JSONResponse(
                status_code=401,
                content={"detail": f"Authentication failed: {str(err)}"}
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
