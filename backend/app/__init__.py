"""
YUGI-AI Backend — Application Package
======================================

The AI Operating System backend built with FastAPI.

Architecture: Clean Architecture (Domain → Application → Infrastructure → Presentation)
Pattern: Repository Pattern with Dependency Injection
API: Versioned REST (/api/v1/) + WebSocket (Socket.IO)

Modules:
    - Auth: JWT + Refresh Token authentication
    - AI Console: Multi-provider AI chat with streaming
    - System Core: User settings and configuration
    - Event Center: Real-time notifications
    - Identity: User profile management
"""

__version__ = "0.1.0"
__app_name__ = "YUGI-AI"
