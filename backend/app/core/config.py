"""
YUGI-AI — Central Configuration
=================================

All application settings managed via Pydantic Settings v2.
Single source of truth for every configurable parameter.

Architecture:
    Environment variables → Pydantic Settings → Validated Python objects

Features:
    - Nested models for each concern (Database, Redis, Auth, CORS, Logging, Telemetry)
    - Environment-specific behavior via Environment enum
    - Flat env var support via env_nested_delimiter="__"
    - Multi-database ready via DatabaseSettings design
    - Singleton pattern via lru_cache

Usage:
    from app.core.config import get_settings

    settings = get_settings()
    print(settings.database.host)  # "localhost"
    print(settings.is_production)  # False

Environment Variables:
    See backend/.env.example for the complete list.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import Environment

# =============================================================================
# Nested Settings Models
# =============================================================================
# Each concern gets its own model. This keeps the root settings clean
# and allows multi-database support by instantiating multiple DatabaseSettings.
# =============================================================================


class DatabaseSettings(BaseSettings):
    """PostgreSQL connection configuration.

    Designed for multi-database support:
    - Primary: main application database (users, chats, settings)
    - Future: read replica, analytics database, etc.

    Connection string assembled as:
        postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}
    """

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    user: str = Field(default="yugi", description="Database username")
    password: str = Field(default="yugi_dev_password", description="Database password")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, ge=1, le=65535, description="Database port")
    name: str = Field(default="yugi_ai", alias="POSTGRES_DB", description="Database name")

    # Connection pool settings
    pool_min_size: int = Field(default=5, ge=1, description="Minimum pool connections")
    pool_max_size: int = Field(default=20, ge=5, description="Maximum pool connections")
    pool_recycle: int = Field(
        default=3600,
        description="Seconds before a connection is recycled (prevents stale connections)",
    )
    echo: bool = Field(
        default=False, description="Echo SQL statements (True in development for debugging)"
    )

    @property
    def async_url(self) -> str:
        """Async connection string for SQLAlchemy with asyncpg driver."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        )

    @property
    def sync_url(self) -> str:
        """Sync connection string for Alembic migrations."""
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        )


class RedisSettings(BaseSettings):
    """Redis connection configuration.

    Redis serves multiple roles:
    - Session store (auth tokens)
    - Rate limiting counters
    - Cache layer (user profiles, settings)
    - Pub/Sub event bus
    """

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    password: str = Field(default="", description="Redis password (empty for no auth)")
    db: int = Field(default=0, ge=0, le=15, description="Redis database number")

    # Connection pool
    pool_min_size: int = Field(default=5, ge=1, description="Minimum pool connections")
    pool_max_size: int = Field(default=20, ge=5, description="Maximum pool connections")

    @property
    def url(self) -> str:
        """Redis connection URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class AuthSettings(BaseSettings):
    """Authentication and encryption settings."""

    model_config = SettingsConfigDict(env_prefix="")

    secret_key: str = Field(
        default="dev-secret-key-do-not-use-in-production-please-change-me-now",
        min_length=32,
        description="JWT signing key. Generate with: openssl rand -hex 64",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(
        default=15, ge=1, description="Access token lifetime in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7, ge=1, description="Refresh token lifetime in days"
    )
    encryption_key: str = Field(
        default="dev-encryption-key-not-for-production-use-generate-real-one",
        description="Fernet key for BYOK API key encryption at rest",
    )


class CorsSettings(BaseSettings):
    """CORS (Cross-Origin Resource Sharing) configuration."""

    model_config = SettingsConfigDict(env_prefix="CORS_")

    origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed origins for cross-origin requests",
    )
    allow_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods",
    )
    allow_headers: list[str] = Field(
        default=["*"],
        description="Allowed request headers",
    )
    allow_credentials: bool = Field(
        default=True,
        description="Allow cookies in cross-origin requests (required for refresh tokens)",
    )

    @field_validator("origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated origins string from env var into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


class LogSettings(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = Field(default="INFO", description="Minimum log level")
    format: str = Field(
        default="console",
        description="Log format: 'json' for production, 'console' for development",
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Ensure log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid_levels:
            msg = f"Invalid log level '{v}'. Must be one of: {valid_levels}"
            raise ValueError(msg)
        return upper

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Ensure log format is valid."""
        valid_formats = {"json", "console"}
        lower = v.lower()
        if lower not in valid_formats:
            msg = f"Invalid log format '{v}'. Must be one of: {valid_formats}"
            raise ValueError(msg)
        return lower


class TelemetrySettings(BaseSettings):
    """OpenTelemetry configuration (disabled by default)."""

    model_config = SettingsConfigDict(env_prefix="OTEL_")

    enabled: bool = Field(
        default=False,
        description="Enable OpenTelemetry tracing and metrics collection",
    )
    service_name: str = Field(
        default="yugi-ai-backend",
        description="Service name reported to the telemetry collector",
    )
    exporter_endpoint: str = Field(
        default="http://localhost:4317",
        description="OTLP exporter endpoint (gRPC)",
    )
    sample_rate: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Trace sampling rate (1.0 = 100%)"
    )


# =============================================================================
# Root Application Settings
# =============================================================================


class AppSettings(BaseSettings):
    """Root application settings.

    Composes all nested settings models into a single configuration object.
    Loaded once at startup and cached via get_settings().

    Env vars:
        ENVIRONMENT=development
        POSTGRES_USER=yugi
        REDIS_HOST=localhost
        SECRET_KEY=...
        LOG_LEVEL=DEBUG
        OTEL_ENABLED=false
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore unknown env vars
        case_sensitive=False,
    )

    # Application
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Current environment (development/staging/production/testing)",
    )
    app_version: str = Field(default="0.1.0", description="Application version")

    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    cors: CorsSettings = Field(default_factory=CorsSettings)
    log: LogSettings = Field(default_factory=LogSettings)
    telemetry: TelemetrySettings = Field(default_factory=TelemetrySettings)

    # Server
    backend_port: int = Field(default=8000, ge=1, le=65535, description="Backend server port")
    backend_workers: int = Field(default=1, ge=1, description="Number of uvicorn workers")

    # ==========================================================================
    # Computed Properties
    # ==========================================================================

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.environment == Environment.TESTING

    @property
    def show_docs(self) -> bool:
        """Whether to enable Swagger/ReDoc documentation endpoints.
        Disabled in production for security."""
        return not self.is_production


# =============================================================================
# Settings Singleton
# =============================================================================


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Load and cache application settings.

    Uses lru_cache to ensure settings are loaded exactly once
    from environment variables / .env file.

    Returns:
        AppSettings: Validated, immutable application configuration.
    """
    return AppSettings()
