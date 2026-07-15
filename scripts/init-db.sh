#!/bin/bash
# =============================================================================
# YUGI-AI — Database Initialization Script
# =============================================================================
# This script runs automatically when the PostgreSQL container starts
# for the first time (mounted in /docker-entrypoint-initdb.d/).
#
# Purpose:
#   1. Enable required PostgreSQL extensions
#   2. Configure database settings for production workloads
#   3. Create application schema
#
# This script runs as the PostgreSQL superuser defined in POSTGRES_USER.
# It only runs on initial database creation, not on subsequent starts.
# =============================================================================

set -euo pipefail

echo "======================================"
echo "  YUGI-AI Database Initialization"
echo "======================================"

# Use the database specified in the environment
DB_NAME="${POSTGRES_DB:-yugi_ai}"

echo "[1/4] Enabling PostgreSQL extensions..."

# uuid-ossp: UUID generation functions (uuid_generate_v4)
# Used for generating primary keys across all tables.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOSQL
echo "  ✓ uuid-ossp"

# pgcrypto: Cryptographic functions (gen_random_uuid, digest)
# Used as a fallback for UUID generation and potential future crypto operations.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
EOSQL
echo "  ✓ pgcrypto"

# pg_trgm: Trigram similarity for fuzzy text search
# Used for searching chat titles, usernames, and future full-text search.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
EOSQL
echo "  ✓ pg_trgm"

echo ""
echo "[2/4] Configuring database settings..."

# Configure connection and statement settings for the application role
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" <<-EOSQL
    -- Set default statement timeout to 30 seconds
    -- Prevents runaway queries from holding connections
    ALTER DATABASE "$DB_NAME" SET statement_timeout = '30s';

    -- Set default lock timeout to 10 seconds
    -- Prevents deadlock-prone transactions from waiting indefinitely
    ALTER DATABASE "$DB_NAME" SET lock_timeout = '10s';

    -- Set timezone to UTC for consistency
    -- All timestamps stored in UTC; conversion happens in the application layer
    ALTER DATABASE "$DB_NAME" SET timezone = 'UTC';
EOSQL
echo "  ✓ Statement timeout: 30s"
echo "  ✓ Lock timeout: 10s"
echo "  ✓ Timezone: UTC"

echo ""
echo "[3/4] Creating application schema..."

# The 'app' schema separates YUGI-AI tables from PostgreSQL system tables.
# This is a best practice for multi-schema databases and future multi-tenancy.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" <<-EOSQL
    -- Create application schema
    CREATE SCHEMA IF NOT EXISTS app;

    -- Set search path so Alembic and SQLAlchemy find tables correctly
    ALTER DATABASE "$DB_NAME" SET search_path TO app, public;

    -- Grant usage to the default user
    GRANT ALL ON SCHEMA app TO "$POSTGRES_USER";
EOSQL
echo "  ✓ Schema 'app' created"
echo "  ✓ Search path configured"

echo ""
echo "[4/4] Verifying installation..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" <<-EOSQL
    -- List installed extensions
    SELECT extname, extversion FROM pg_extension WHERE extname IN ('uuid-ossp', 'pgcrypto', 'pg_trgm');

    -- List schemas
    SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('app', 'public');
EOSQL

echo ""
echo "======================================"
echo "  YUGI-AI Database Ready!"
echo "======================================"
echo "  Database: $DB_NAME"
echo "  Extensions: uuid-ossp, pgcrypto, pg_trgm"
echo "  Schema: app"
echo "======================================"
