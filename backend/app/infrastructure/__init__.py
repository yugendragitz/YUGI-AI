"""
YUGI-AI — Infrastructure Layer
================================

External system implementations (adapters).
This layer provides concrete implementations for domain interfaces.

Contains:
    - Database: SQLAlchemy async engine, session management, base ORM model
    - Future: Redis cache adapter, email service, file storage, AI provider adapters

Dependency Rule:
    Infrastructure implements interfaces defined in domain.
    Infrastructure imports from: core, domain
    Infrastructure is imported by: api (for dependency injection)
"""
