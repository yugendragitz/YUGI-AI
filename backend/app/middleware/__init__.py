"""
YUGI-AI — Middleware Package
==============================

ASGI middleware for request processing pipeline.

Middleware execution order (outermost → innermost):
    1. CORS (handled by FastAPI/Starlette CORSMiddleware)
    2. Security Headers
    3. Correlation ID → generates/extracts ID, binds to structlog
    4. Exception Handler → catches all errors, returns structured JSON

Each middleware is a Starlette BaseHTTPMiddleware or raw ASGI middleware.
"""
