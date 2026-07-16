"""
YUGI-AI — Structured Logging
==============================

Configures structlog for structured, JSON-formatted logging (ADR-012).

Output Modes:
    - Production:  JSON lines to stdout → ingested by ELK / CloudWatch / Datadog
    - Development: Colored console output with padded alignment → human readable

Features:
    - Correlation ID automatically bound to every log entry (via context vars)
    - Processor pipeline: timestamp, log level, caller info, sensitive data redaction
    - stdlib logging routed through structlog (captures SQLAlchemy, uvicorn, etc.)
    - Thread-safe and async-safe via contextvars

Usage:
    from app.core.logging import setup_logging, get_logger

    setup_logging(log_level="DEBUG", log_format="console")

    logger = get_logger(__name__)
    logger.info("User logged in", user_id="abc-123")
    # Output: 2026-07-16T04:00:00Z [info] User logged in  user_id=abc-123 correlation_id=...
"""

import logging
import sys

import structlog

# =============================================================================
# Sensitive Field Redaction
# =============================================================================
# Fields in this set will have their values replaced with "[REDACTED]"
# in all log output. Prevents accidental PII/secret leakage to log stores.
REDACTED_FIELDS = frozenset(
    {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "secret_key",
        "encryption_key",
        "api_key",
        "authorization",
    }
)


def _redact_sensitive_fields(
    _logger: logging.Logger,
    _method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Structlog processor that redacts sensitive field values.

    Scans all key-value pairs in the log event and replaces values
    of known sensitive fields with "[REDACTED]".
    """
    for key in event_dict:
        if key.lower() in REDACTED_FIELDS:
            event_dict[key] = "[REDACTED]"
    return event_dict


def _add_app_context(
    _logger: logging.Logger,
    _method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Add application context to every log entry."""
    event_dict.setdefault("app", "yugi-ai")
    return event_dict


# =============================================================================
# Setup Functions
# =============================================================================


def setup_logging(log_level: str = "INFO", log_format: str = "console") -> None:
    """Configure structlog and stdlib logging.

    Must be called once at application startup (in lifespan).

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format — "json" for production, "console" for development.
    """
    # Determine the renderer based on format
    if log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            pad_event=40,
        )

    # Shared processors applied to ALL log entries
    shared_processors: list[structlog.types.Processor] = [
        # Add log level as a string field
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # ISO 8601 timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exception tracebacks
        structlog.processors.format_exc_info,
        # Merge context vars (correlation_id, etc.) into the event dict
        structlog.contextvars.merge_contextvars,
        # Redact sensitive fields
        _redact_sensitive_fields,
        # Add app context
        _add_app_context,
    ]

    # Configure structlog
    structlog.configure(
        processors=[
            *shared_processors,
            # Prepare for stdlib-compatible output
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
        context_class=dict,
    )

    # Configure stdlib logging to route through structlog
    # This captures logs from uvicorn, SQLAlchemy, httpx, etc.
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    # Root handler — all output goes to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if log_level.upper() == "DEBUG" else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    The returned logger automatically includes any context vars
    bound in the current request scope (e.g., correlation_id).

    Args:
        name: Logger name (typically __name__). If None, uses the root logger.

    Returns:
        A structlog BoundLogger instance.

    Usage:
        logger = get_logger(__name__)
        logger.info("Processing request", endpoint="/api/v1/health")
    """
    return structlog.get_logger(name)
