# =============================================================================
# YUGI-AI Frontend — Multi-Stage Dockerfile
# =============================================================================
# Stages:
#   1. base:        Common Node.js setup
#   2. deps:        Install dependencies (cached layer)
#   3. development: Dev server with hot reload (next dev)
#   4. builder:     Production build (next build)
#   5. production:  Minimal production image (next start)
#
# Build targets:
#   docker build --target development -t yugi-frontend:dev .
#   docker build --target production -t yugi-frontend:prod .
#
# NOTE: This Dockerfile requires a Next.js project to be initialized.
#       Run Module 13 (Frontend Scaffolding) before building.
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Base — Common Node.js setup
# ---------------------------------------------------------------------------
FROM node:20-alpine AS base

# Metadata
LABEL maintainer="YUGI-AI Team"
LABEL description="YUGI-AI Frontend — Next.js Application"
LABEL version="0.1.0"

# Install system dependencies
# libc6-compat: required for some native Node.js modules on Alpine
RUN apk add --no-cache libc6-compat

WORKDIR /app

# ---------------------------------------------------------------------------
# Stage 2: Dependencies — Install and cache node_modules
# ---------------------------------------------------------------------------
FROM base AS deps

# Copy package files first for Docker layer caching
# This layer is only rebuilt when package.json or package-lock.json changes
COPY package.json package-lock.json* ./

# Install dependencies
# --frozen-lockfile ensures reproducible builds (fails if lockfile is outdated)
RUN npm ci

# ---------------------------------------------------------------------------
# Stage 3: Development — Hot reload server
# ---------------------------------------------------------------------------
FROM base AS development

# Copy installed dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application source
# In development, src/ and public/ are overridden by volume mounts
COPY . .

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

USER nextjs

EXPOSE 3000

# Next.js dev server with Fast Refresh
# Binds to 0.0.0.0 so Docker can route traffic to the container
CMD ["npx", "next", "dev", "--hostname", "0.0.0.0", "--port", "3000"]

# ---------------------------------------------------------------------------
# Stage 4: Builder — Production build
# ---------------------------------------------------------------------------
FROM base AS builder

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build-time environment variables for Next.js
# These are baked into the static build and available in the browser
ARG NEXT_PUBLIC_API_URL=http://localhost/api
ARG NEXT_PUBLIC_WS_URL=ws://localhost/ws
ARG NEXT_PUBLIC_APP_NAME=YUGI-AI
ARG NEXT_PUBLIC_APP_VERSION=0.1.0

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME
ENV NEXT_PUBLIC_APP_VERSION=$NEXT_PUBLIC_APP_VERSION

# Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

# Build production bundle
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 5: Production — Minimal runtime image
# ---------------------------------------------------------------------------
FROM base AS production

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application from builder stage
# Next.js outputs:
#   .next/standalone/ — self-contained server with node_modules
#   .next/static/     — static assets (JS, CSS, images)
#   public/           — static public files
COPY --from=builder /app/public ./public

# Use Next.js standalone output for minimal image size
# This requires output: 'standalone' in next.config.ts
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Start Next.js production server
# Uses the standalone server which includes only necessary dependencies
CMD ["node", "server.js"]
