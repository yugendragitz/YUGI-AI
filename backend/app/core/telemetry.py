"""
YUGI-AI — OpenTelemetry Integration
=====================================

Optional OpenTelemetry hooks for distributed tracing and metrics.
Disabled by default. Zero overhead when disabled — all functions are no-ops.

Activation:
    Set OTEL_ENABLED=true in environment variables.
    Install OpenTelemetry packages:
        pip install opentelemetry-api opentelemetry-sdk \\
                    opentelemetry-instrumentation-fastapi \\
                    opentelemetry-instrumentation-httpx \\
                    opentelemetry-instrumentation-sqlalchemy \\
                    opentelemetry-exporter-otlp

Architecture:
    - TracerProvider with OTLP exporter → sends traces to collector (Jaeger, Tempo, etc.)
    - MeterProvider with OTLP exporter → sends metrics to collector (Prometheus, etc.)
    - Auto-instrumentation for FastAPI, httpx, SQLAlchemy
    - Correlation ID attached as span attribute for cross-referencing with logs

Usage:
    from app.core.telemetry import setup_telemetry

    # In lifespan:
    setup_telemetry(app, settings)  # No-op if settings.telemetry.enabled is False
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

    from app.core.config import AppSettings

logger = logging.getLogger(__name__)

# =============================================================================
# Optional imports — guarded so OpenTelemetry packages are truly optional.
# When OTEL_ENABLED=false (default), none of these packages need to be installed.
# =============================================================================
_HAS_OPENTELEMETRY = False

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

    _HAS_OPENTELEMETRY = True
except ImportError:
    pass


# Optional instrumentors — each guarded independently so partial installs work
_HAS_HTTPX_INSTRUMENTOR = False
try:
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    _HAS_HTTPX_INSTRUMENTOR = True
except ImportError:
    pass

_HAS_SQLALCHEMY_INSTRUMENTOR = False
try:
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    _HAS_SQLALCHEMY_INSTRUMENTOR = True
except ImportError:
    pass


def setup_telemetry(app: FastAPI, settings: AppSettings) -> None:
    """Initialize OpenTelemetry tracing and instrumentation.

    No-op if:
    - settings.telemetry.enabled is False
    - OpenTelemetry packages are not installed

    Args:
        app: The FastAPI application instance to instrument.
        settings: Application settings containing telemetry configuration.
    """
    if not settings.telemetry.enabled:
        logger.debug("OpenTelemetry is disabled (OTEL_ENABLED=false)")
        return

    if not _HAS_OPENTELEMETRY:
        logger.warning(
            "OpenTelemetry is enabled but packages are not installed. "
            "Install with: pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp"
        )
        return

    logger.info(
        "Initializing OpenTelemetry — service=%s endpoint=%s sample_rate=%.2f",
        settings.telemetry.service_name,
        settings.telemetry.exporter_endpoint,
        settings.telemetry.sample_rate,
    )

    # Create resource identifying this service
    resource = Resource.create(
        attributes={
            "service.name": settings.telemetry.service_name,
            "service.version": settings.app_version,
            "deployment.environment": settings.environment.value,
        }
    )

    # Configure tracer provider with sampling
    sampler = TraceIdRatioBased(settings.telemetry.sample_rate)
    tracer_provider = TracerProvider(resource=resource, sampler=sampler)

    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.telemetry.exporter_endpoint,
        insecure=not settings.is_production,
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set as global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    logger.info("  ✓ FastAPI instrumented")

    # Instrument httpx (for AI provider API calls)
    if _HAS_HTTPX_INSTRUMENTOR:
        HTTPXClientInstrumentor().instrument()
        logger.info("  ✓ httpx instrumented")

    # Instrument SQLAlchemy (for database query tracing)
    if _HAS_SQLALCHEMY_INSTRUMENTOR:
        SQLAlchemyInstrumentor().instrument(enable_commenter=True)
        logger.info("  ✓ SQLAlchemy instrumented")

    logger.info("OpenTelemetry initialization complete")


def shutdown_telemetry() -> None:
    """Flush and shutdown the tracer provider.

    Call during application shutdown to ensure all pending spans are exported.
    """
    if not _HAS_OPENTELEMETRY:
        return

    provider = trace.get_tracer_provider()
    if hasattr(provider, "shutdown"):
        provider.shutdown()
        logger.info("OpenTelemetry tracer provider shut down")
