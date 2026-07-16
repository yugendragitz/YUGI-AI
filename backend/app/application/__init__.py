"""
YUGI-AI — Application Layer
==============================

Use case orchestration layer. Services here coordinate domain entities,
repositories, and external services to fulfill business use cases.

Dependency Rule:
    Application layer imports from: domain, core
    Application layer NEVER imports from: infrastructure, api, middleware

Services receive their dependencies via constructor injection.
"""
