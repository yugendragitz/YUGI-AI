"""
YUGI-AI — API Presentation Layer
==================================

HTTP/WebSocket interface. This is the outermost layer in Clean Architecture.

Contains:
    - dependencies.py: DI container for FastAPI Depends()
    - v1/: Versioned API routers and endpoints

Dependency Rule:
    API layer imports from: all other layers
    API layer is NOT imported by: domain, application, infrastructure
"""
