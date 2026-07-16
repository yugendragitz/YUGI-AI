"""
YUGI-AI — Common Type Aliases
==============================

Shared type definitions used across all architecture layers.
Keeps type annotations consistent and reduces import verbosity.

Usage:
    from app.core.types import EntityId, JSON

    class User:
        id: EntityId
        metadata: JSON
"""

import uuid
from typing import Any

# =============================================================================
# Entity Types
# =============================================================================
EntityId = uuid.UUID
"""Primary key type for all domain entities. UUID v4 for collision-proof,
non-sequential, information-safe identifiers (ADR-014)."""

# =============================================================================
# Data Types
# =============================================================================
JSON = dict[str, Any]
"""Generic JSON-compatible dictionary. Used for metadata fields,
JSONB columns, and unstructured configuration data."""

Headers = dict[str, str]
"""HTTP header mapping. Used for request/response header manipulation."""

# =============================================================================
# Callback Types
# =============================================================================
# These will be expanded as we add event handlers, middleware hooks, etc.
