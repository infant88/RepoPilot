# DemoStore API

A lightweight sample FastAPI service used for demonstrating RepoPilot repository indexing, code navigation, debugging, and security analysis.

## Architecture
- `backend/config/settings.py`: Centralized configuration and environment settings (JWT_SECRET, DATABASE_URL).
- `backend/auth/jwt.py`: JWT generation, cryptographic signing (HMAC-SHA256), and verification.
- `backend/auth/middleware.py`: Custom ASGI AuthenticationMiddleware validating `Authorization: Bearer <token>` and handling 401 Unauthorized responses.
- `backend/routes/auth.py`: Endpoint handlers for `/api/v1/auth/login` and user authentication.
- `backend/main.py`: Application entrypoint, CORS setup, middleware pipeline.

## Known Issue & Debug Scenario
When running under Docker (`docker-compose up`), requests may return `401 Unauthorized`.
Investigate `backend/config/settings.py`, `backend/auth/middleware.py`, and `docker-compose.yml` to diagnose secret mismatch or missing environment variables.
