# YUGI-AI Architecture Decision Records

> **Version**: 1.0.0
> **Status**: Living document — updated with every major decision.
> **Last Updated**: 2026-07-15

---

## How to Read This Document

Each decision follows a consistent format:

| Field | Description |
|-------|-------------|
| **Status** | `ACCEPTED` · `PROPOSED` · `DEPRECATED` · `SUPERSEDED` |
| **Date** | When the decision was made |
| **Problem** | What problem are we solving? |
| **Alternatives** | What options were considered? |
| **Chosen Solution** | What did we pick? |
| **Reason** | Why this over alternatives? |
| **Tradeoffs** | What are we giving up? |
| **Future Impact** | How does this affect future decisions? |

---

## Table of Contents

1. [ADR-001: Frontend Framework](#adr-001-frontend-framework)
2. [ADR-002: Backend Framework](#adr-002-backend-framework)
3. [ADR-003: Database Selection](#adr-003-database-selection)
4. [ADR-004: Authentication Strategy](#adr-004-authentication-strategy)
5. [ADR-005: API Key Management (BYOK)](#adr-005-api-key-management-byok)
6. [ADR-006: AI Provider Abstraction](#adr-006-ai-provider-abstraction)
7. [ADR-007: Voice Provider Abstraction](#adr-007-voice-provider-abstraction)
8. [ADR-008: State Management](#adr-008-state-management)
9. [ADR-009: Real-Time Communication](#adr-009-real-time-communication)
10. [ADR-010: Styling System](#adr-010-styling-system)
11. [ADR-011: Backend Architecture Pattern](#adr-011-backend-architecture-pattern)
12. [ADR-012: Logging Strategy](#adr-012-logging-strategy)
13. [ADR-013: Caching Strategy](#adr-013-caching-strategy)
14. [ADR-014: ID Generation Strategy](#adr-014-id-generation-strategy)
15. [ADR-015: API Versioning](#adr-015-api-versioning)
16. [ADR-016: Avatar System](#adr-016-avatar-system)
17. [ADR-017: Error Handling Strategy](#adr-017-error-handling-strategy)
18. [ADR-018: Deployment Architecture](#adr-018-deployment-architecture)
19. [ADR-019: Rate Limiting Strategy](#adr-019-rate-limiting-strategy)
20. [ADR-020: Animation Libraries](#adr-020-animation-libraries)
21. [ADR-021: Event Bus Architecture](#adr-021-event-bus-architecture)
22. [ADR-022: File Storage Abstraction](#adr-022-file-storage-abstraction)
23. [ADR-023: Request Tracing](#adr-023-request-tracing)
24. [ADR-024: Module Naming Convention](#adr-024-module-naming-convention)
25. [ADR-025: Database ORM and Migrations](#adr-025-database-orm-and-migrations)

---

## ADR-001: Frontend Framework

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

We need a frontend framework that supports server-side rendering (for SEO on the landing page), client-side interactivity (for the OS shell), code splitting (for modular architecture), and can scale to millions of users.

### Alternatives

| Option | Pros | Cons |
|--------|------|------|
| **Next.js 15 (App Router)** | SSR/SSG, React Server Components, streaming, built-in routing, massive ecosystem | Complex mental model (server vs client), larger bundle |
| **Vite + React** | Fast dev server, simple, lightweight | No SSR out of box, manual routing, no streaming SSR |
| **Remix** | Nested routes, loaders, progressive enhancement | Smaller ecosystem, less mature than Next.js |
| **Astro** | Multi-framework, islands, great for content | Not designed for app-like experiences |

### Chosen Solution

**Next.js 15 with App Router**

### Reason

1. **App Router** enables parallel routes — essential for the OS shell metaphor where sidebar, topbar, and content area are independent route segments.
2. **React Server Components** reduce client-side JavaScript for non-interactive content (settings pages, profile).
3. **Streaming SSR** enables progressive rendering of the AI Console while waiting for data.
4. **Built-in API routes** can proxy requests to our FastAPI backend, solving CORS in development.
5. **Vercel-optimized** but deployable anywhere via Docker (cloud-agnostic).

### Tradeoffs

- Increased complexity from the server/client component boundary.
- Larger initial bundle compared to Vite + React.
- App Router is newer, some patterns are still evolving.

### Future Impact

- PWA support via `next-pwa` for offline capability.
- React Server Components will become more powerful — we benefit automatically.
- Potential micro-frontend architecture using Module Federation in Next.js.

---

## ADR-002: Backend Framework

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

We need a backend that handles REST APIs, WebSocket connections for real-time AI streaming, integrates with multiple AI providers asynchronously, and supports production-grade performance.

### Alternatives

| Option | Pros | Cons |
|--------|------|------|
| **FastAPI** | Native async, auto OpenAPI docs, Pydantic validation, Python AI ecosystem | Python GIL for CPU-bound work |
| **Express.js (Node)** | Same language as frontend, huge ecosystem | No built-in validation, callback patterns |
| **NestJS (Node)** | Enterprise patterns, TypeScript, DI | Heavy, opinionated, learning curve |
| **Go (Gin/Fiber)** | Blazing fast, goroutines, compiled | Smaller AI ecosystem, verbose |
| **Django** | Mature, ORM, admin panel | Synchronous by default, heavy |

### Chosen Solution

**FastAPI (Python 3.12+)**

### Reason

1. **Native async/await** matches our I/O-bound workload (AI API calls, database, Redis).
2. **Pydantic v2** for request/response validation — DTOs are enforced at framework level.
3. **Auto-generated OpenAPI docs** — every endpoint is self-documenting.
4. **Python ecosystem** — direct access to OpenAI, Anthropic, Google AI SDKs without bridge layers.
5. **3-5x throughput** vs sync frameworks (Django, Flask) under concurrent load.
6. **WebSocket support** is first-class with `python-socketio`.

### Tradeoffs

- Python is slower than Go/Rust for CPU-bound tasks (mitigated: our workload is I/O-bound).
- GIL prevents true parallelism (mitigated: async handles concurrency, Celery handles background tasks).
- Larger memory footprint per process vs Go.

### Future Impact

- Celery workers for background tasks (memory summarization, file processing).
- Potential to add a Go microservice for performance-critical paths (device management).
- Python ML libraries available directly (PyTorch, transformers) for local model support.

---

## ADR-003: Database Selection

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

We need a database that handles relational data (users, sessions, chats), semi-structured data (AI memory, metadata), full-text search, and can scale vertically and horizontally.

### Alternatives

| Option | Pros | Cons |
|--------|------|------|
| **PostgreSQL 16** | JSONB, full-text search, pgvector, row-level security, mature | Requires tuning for scale |
| **MongoDB** | Flexible schema, document model | No ACID by default, join performance, consistency concerns |
| **MySQL 8** | Widely deployed, simple | Weaker JSON support, no pgvector equivalent |
| **CockroachDB** | Distributed PostgreSQL-compatible | Complexity, cost, overkill for Phase 1 |

### Chosen Solution

**PostgreSQL 16**

### Reason

1. **JSONB** columns for flexible metadata on chats, messages, AI memory — no schema migration for new fields.
2. **pgvector extension** for future RAG (Retrieval-Augmented Generation) with AI memory embeddings.
3. **Partial indexes** for performance (e.g., index only unread notifications, active sessions).
4. **Row-level security** for future multi-tenancy.
5. **Logical replication** for read replicas when we scale.
6. **ACID compliance** — critical for financial operations, session management, audit logs.

### Tradeoffs

- Vertical scaling has limits (mitigated: read replicas, connection pooling, caching layer).
- More complex setup than SQLite for local dev (mitigated: Docker handles this).
- Schema migrations required for structural changes (mitigated: Alembic auto-generates).

### Future Impact

- pgvector enables vector similarity search for AI memory retrieval.
- Logical replication enables read replicas for scaling read-heavy workloads.
- Row-level security enables multi-tenant architecture without application-level checks.

---

## ADR-004: Authentication Strategy

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

We need authentication that works across browsers and future mobile apps, supports multiple devices, enables session management, and is resistant to common attacks (XSS, CSRF, token theft).

### Alternatives

| Option | Pros | Cons |
|--------|------|------|
| **JWT + Refresh Token (Rotation)** | Stateless access, revocable sessions, industry standard | Requires careful token storage |
| **Session Cookies (Server-Side)** | Simple, server controls everything | Doesn't scale horizontally without sticky sessions |
| **OAuth2 + OIDC Only** | Delegated auth, SSO | Requires external provider, complex for email/password |
| **Passport.js / NextAuth** | Ready-made, many providers | Node.js only, doesn't work with FastAPI backend |

### Chosen Solution

**JWT access tokens (in-memory) + Refresh tokens (httpOnly cookie, rotated)**

### Reason

1. **Access token in memory only** — XSS cannot steal it (never in localStorage).
2. **Refresh token in httpOnly cookie** — JavaScript cannot access it, CSRF mitigated by SameSite=Lax.
3. **Token rotation** — each refresh invalidates the previous token. Reuse of old token = theft detected → revoke all sessions.
4. **15-minute access token** — minimal damage window if somehow leaked.
5. **Sessions table** — enables "active sessions" view, per-device logout, admin revocation.
6. **OAuth-ready schema** — `oauth_accounts` table designed, callback routes can be added without schema changes.

### Tradeoffs

- More complex than simple session cookies.
- Requires refresh logic on the frontend (401 → refresh → retry).
- Token rotation adds database writes on every refresh.

### Future Impact

- OAuth providers (Google, GitHub) plug into the `oauth_accounts` table.
- Mobile apps use the same JWT flow (cookies → bearer token in mobile).
- Admin panel can view and revoke sessions per user.

---

## ADR-005: API Key Management (BYOK)

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

Users need to provide their own API keys for various AI providers. Keys must be stored securely, encrypted at rest, and never exposed to the frontend after submission.

### Alternatives

| Option | Pros | Cons |
|--------|------|------|
| **Fernet symmetric encryption (server-side)** | Simple, fast, Python built-in (cryptography lib), key rotation possible | Single encryption key to protect |
| **AES-256-GCM** | Industry standard, authenticated encryption | More complex implementation |
| **Client-side encryption** | Server never sees plaintext | Key management on client is unreliable, can't validate keys server-side |
| **AWS KMS / Vault** | Hardware-backed, audit trail | External dependency, cost, complexity for Phase 1 |

### Chosen Solution

**Fernet symmetric encryption with server-side master key**

### Reason

1. **Fernet** uses AES-128-CBC with HMAC — authenticated encryption prevents tampering.
2. **Python `cryptography` library** — well-maintained, FIPS-capable.
3. **Master key from environment variable** — rotatable without code changes.
4. **Key rotation**: Re-encrypt all keys when master key rotates (background task).
5. **Simple**: No external service dependency (cloud-agnostic).

### Tradeoffs

- Single master key is a single point of failure (mitigated: can migrate to KMS in Phase 2+).
- All keys are decryptable by anyone with the master key (mitigated: environment variable protection, container isolation).
- Fernet uses AES-128 not AES-256 (sufficient for API key encryption; these aren't state secrets).

### Future Impact

- Migration path to AWS KMS / HashiCorp Vault when infrastructure matures.
- Key rotation mechanism can be extended to rotate provider keys themselves (remind users to rotate).
- Audit log tracks when keys are accessed/validated.

---

## ADR-006: AI Provider Abstraction

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

The system must support multiple AI providers (OpenAI, Claude, Gemini, OpenRouter, Ollama, LM Studio) with the ability to add new ones without modifying existing code. Users select their provider and model from System Core.

### Alternatives

| Option | Pros | Cons |
|--------|------|------|
| **Abstract interface + Factory Pattern** | Clean, SOLID, each provider is independent | More files, slightly more boilerplate |
| **LangChain** | Pre-built provider support, chains, agents | Heavy dependency, abstracts too much, version churn |
| **LiteLLM** | Unified API for 100+ providers | External dependency, black box, debugging difficulty |
| **Direct SDK calls** | Simple, no abstraction overhead | Tight coupling, changing providers requires rewriting |

### Chosen Solution

**Custom abstract interface + Factory Pattern + Model Registry**

### Reason

1. **No external dependency risk** — LangChain and LiteLLM have frequent breaking changes.
2. **Full control** over streaming behavior, error handling, and token counting per provider.
3. **Factory pattern** — adding a provider = implement interface + register. Zero changes to existing code.
4. **Model Registry** — centralized list of available models per provider, queryable from System Core UI.
5. **SOLID**: Open for extension (new providers), closed for modification (existing code unchanged).

### Tradeoffs

- More initial code than using LangChain/LiteLLM.
- We maintain our own provider implementations (mitigated: most providers have excellent SDKs).
- Feature parity across providers requires per-provider effort (streaming, function calling, etc.).

### Future Impact

- Each provider can have custom capabilities (function calling, vision, etc.) exposed through interface extensions.
- Model registry can be updated via config without code deployment.
- Community can contribute provider implementations as plugins.

---

## ADR-007: Voice Provider Abstraction

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

Phase 1 uses browser-native Web Speech API, but the architecture must support ElevenLabs, Azure Speech, Google Speech, and OpenAI Voice in the future without frontend changes.

### Alternatives

| Option | Pros | Cons |
|--------|------|------|
| **Frontend abstraction (provider interface in React)** | Zero backend calls for Web Speech | Mixes provider logic with UI |
| **Backend abstraction (same as AI providers)** | Consistent pattern, server-side processing | Adds latency for Web Speech (unnecessary roundtrip) |
| **Hybrid: Frontend interface with backend fallback** | Best of both worlds | More complex |

### Chosen Solution

**Frontend abstraction layer with provider interface**

### Reason

1. **Web Speech API is browser-native** — sending audio to the backend and back adds unnecessary latency.
2. **Future cloud providers** (ElevenLabs, Azure) can be called from either frontend or backend via the same interface.
3. **Provider interface on frontend** keeps voice logic encapsulated in the `features/voice/` module.
4. **Backend provides voice configuration** via System Core settings — which provider, which voice ID.

### Tradeoffs

- Cloud voice providers called from frontend expose API keys (mitigated: proxy through backend for cloud providers).
- Web Speech API quality varies by browser (mitigated: fall back to cloud provider if available).
- More complex than just using Web Speech API directly.

### Future Impact

- ElevenLabs/Azure calls will proxy through the backend to protect API keys.
- Voice settings stored in user preferences, synchronized via System Core API.
- Real-time voice conversation (duplex streaming) will require WebSocket voice channel.

---

## ADR-008: State Management

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

We need client-side state management that handles auth state, AI Console conversations, settings, notifications, and WebSocket connection state without prop-drilling or over-rendering.

### Alternatives

| Option | Pros | Cons |
|--------|------|------|
| **Zustand** | Tiny (1KB), no boilerplate, selector-based re-renders, TypeScript-first | No devtools as mature as Redux |
| **Redux Toolkit** | Mature, great devtools, middleware ecosystem | Boilerplate heavy, overkill for our scale |
| **Jotai** | Atomic, bottom-up, great for derived state | Different mental model, less structured |
| **React Context** | Built-in, no dependency | Re-renders entire tree, no selectors |
| **TanStack Query** | Perfect for server state | Not designed for client-only state |

### Chosen Solution

**Zustand for client state + TanStack Query for server state**

### Reason

1. **Zustand**: 1KB, no providers needed, selector-based re-renders prevent unnecessary updates.
2. **TanStack Query**: Handles server state (API calls, caching, revalidation, optimistic updates).
3. **Separation**: Client state (UI state, WebSocket connection) in Zustand. Server state (user data, chats, settings) in TanStack Query.
4. **Per-feature stores**: `authStore`, `consoleStore`, `settingsStore` — each module manages its own state.

### Tradeoffs

- Two state management solutions (Zustand + TanStack Query) instead of one.
- Developers must decide which to use for each piece of state.

### Future Impact

- Zustand stores can be persisted to localStorage for offline support.
- TanStack Query's cache can be pre-populated during SSR.
- Each "OS module" gets its own isolated store — true module independence.

---

## ADR-009: Real-Time Communication

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

AI responses must stream token-by-token to the client. Notifications should be pushed in real-time. Future features (device control, automation) will need bidirectional real-time communication.

### Alternatives

| Option | Pros | Cons |
|--------|------|------|
| **Socket.IO** | Auto-reconnection, rooms, namespaces, fallback to polling | Slightly heavier than raw WebSocket |
| **Raw WebSocket** | Lightweight, native | No auto-reconnect, no rooms, manual binary framing |
| **Server-Sent Events (SSE)** | Simple, HTTP-based, auto-reconnect | Unidirectional (server→client only) |
| **gRPC Streaming** | Efficient binary, strong typing | Complex setup, not browser-native |

### Chosen Solution

**Socket.IO (python-socketio + socket.io-client)**

### Reason

1. **Auto-reconnection** with exponential backoff — critical for mobile/unstable connections.
2. **Rooms** — each chat gets a room, enabling targeted message delivery.
3. **Namespaces** — separate `/console`, `/events`, `/devices` (future) without interference.
4. **Fallback to HTTP long-polling** — works behind restrictive firewalls.
5. **Same library** on both frontend (socket.io-client) and backend (python-socketio).

### Tradeoffs

- ~25KB additional client bundle vs raw WebSocket.
- Socket.IO protocol is not compatible with raw WebSocket clients.
- Slightly more overhead per message than raw WebSocket.

### Future Impact

- Device control namespace (`/devices`) for real-time hardware communication.
- Automation namespace (`/automation`) for live trigger/action streams.
- Redis adapter enables horizontal scaling (multiple Socket.IO servers sharing state).

---

## ADR-010: Styling System

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

We need a styling system that supports our complex design system (glassmorphism, neon effects, particles), provides utility classes for rapid development, and generates minimal CSS.

### Alternatives

| Option | Pros | Cons |
|--------|------|------|
| **TailwindCSS v4** | CSS-first config, JIT, tiny bundle, utility-first | Learning curve for complex effects |
| **TailwindCSS v3** | Stable, widely documented | Config-heavy, deprecated soon |
| **CSS Modules** | Scoped, no runtime, co-located | Verbose, no utilities, naming overhead |
| **Styled Components** | Dynamic styles, JS-powered | Runtime cost, SSR complexity |
| **Vanilla CSS + Custom Properties** | Full control, no dependency | No utilities, verbose, manual responsive |

### Chosen Solution

**TailwindCSS v4 + CSS custom properties for design tokens**

### Reason

1. **v4's CSS-first config** — design tokens defined in CSS (`@theme`), not JavaScript.
2. **JIT engine** — generates only used classes, ~10KB CSS in production.
3. **Custom properties integration** — our design tokens live as CSS vars, Tailwind references them.
4. **Utility-first** — rapid prototyping without leaving the component file.
5. **Custom components** — glassmorphism effects defined as custom Tailwind utilities/components.

### Tradeoffs

- Complex glass/neon effects still require custom CSS alongside Tailwind.
- Team must learn Tailwind v4's new CSS-first configuration.
- Some dynamic styles (runtime theme changes) may need CSS custom properties directly.

### Future Impact

- Theme switching via CSS custom properties is already built into the design system.
- Tailwind v4's `@theme` block aligns perfectly with our token architecture.
- Custom utilities can be shared as a Tailwind plugin if we open-source the design system.

---

## ADR-011: Backend Architecture Pattern

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

The backend needs clear separation of concerns to allow independent testing, replacement of infrastructure components (database, cache, AI providers), and maintainable code at scale.

### Alternatives

| Option | Pros | Cons |
|--------|------|------|
| **Clean Architecture** | Domain isolation, testable, replaceable infrastructure | More layers, more files |
| **MVC** | Simple, well-understood | Domain logic bleeds into controllers, hard to test |
| **Hexagonal (Ports & Adapters)** | Similar to Clean, explicit ports | Often confused with Clean Arch, same tradeoffs |
| **CQRS** | Optimized reads/writes, event sourcing ready | Overkill for Phase 1, complexity |

### Chosen Solution

**Clean Architecture (4 layers: Presentation → Application → Domain → Infrastructure)**

### Reason

1. **Domain layer** has zero dependencies — pure business logic, testable without database/API.
2. **Infrastructure layer** implements domain interfaces — swap PostgreSQL for MongoDB by implementing new repositories.
3. **Application layer** orchestrates use cases — contains no I/O, only coordinates domain and infrastructure.
4. **Presentation layer** (API routes) handles HTTP/WebSocket concerns only — serialization, validation, routing.
5. **Dependency injection** via FastAPI's `Depends()` — clean, framework-supported, no third-party DI container.

### Tradeoffs

- More files and indirection than a flat MVC structure.
- New developers need to understand the layer boundaries.
- Simple CRUD operations feel over-engineered (acceptable: consistency > convenience).

### Future Impact

- CQRS can be added on top of Clean Architecture when read/write patterns diverge.
- Event sourcing can be layered into the domain without touching infrastructure.
- Microservice extraction is trivial — each feature module is already self-contained.

---

## ADR-012: Logging Strategy

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

We need structured, searchable, JSON-formatted logs with correlation IDs, severity levels, and automatic sensitive data redaction.

### Chosen Solution

**structlog (Python) with JSON output**

### Reason

1. **Structured key-value pairs** — every log entry is a JSON object, searchable by any field.
2. **Correlation ID binding** — bind request ID once, automatically included in every log within that request.
3. **Processor pipeline** — add/remove processors (redaction, enrichment) without changing log call sites.
4. **Performance** — structlog is faster than stdlib logging with equivalent functionality.

### Tradeoffs

- JSON logs are less human-readable in local development (mitigated: dev mode uses colored console output).
- Additional dependency (mitigated: structlog is stable, well-maintained, 10M+ downloads/month).

### Future Impact

- Log aggregation (ELK, CloudWatch, Datadog) ingests JSON natively.
- Correlation IDs enable distributed tracing when we add microservices.
- Sensitive data processors prevent accidental PII leakage to log stores.

---

## ADR-013: Caching Strategy

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

We need caching for user sessions, rate limiting counters, frequently accessed data (user profiles, settings), and WebSocket connection state.

### Chosen Solution

**Redis 7 (multi-purpose: cache + sessions + rate limiting + Pub/Sub)**

### Reason

1. **Single service, multiple roles** — reduces infrastructure complexity.
2. **Atomic operations** — `INCR`, `EXPIRE` for rate limiting without race conditions.
3. **Pub/Sub** — event bus for real-time notifications between services.
4. **Persistence** — AOF/RDB snapshots prevent data loss on restart.
5. **Connection pooling** — `redis-py` async with connection pool handles high concurrency.

### Tradeoffs

- Single Redis instance is a SPOF (mitigated: Redis Sentinel/Cluster in production).
- Memory-bound (mitigated: TTLs on all keys, eviction policies configured).
- Mixing concerns in one Redis (mitigated: use key prefixes and logical databases).

### Future Impact

- Redis Cluster for horizontal scaling when needed.
- Redis Streams as an alternative to Pub/Sub for reliable event delivery.
- Potential split: separate Redis instances for cache vs. sessions when traffic warrants it.

---

## ADR-014: ID Generation Strategy

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

We need unique identifiers for all entities that are safe for distributed systems, don't leak information (sequential IDs reveal count), and perform well as database primary keys.

### Chosen Solution

**UUID v4 (random) stored as PostgreSQL `uuid` type**

### Reason

1. **No information leakage** — can't guess user count, chat count, etc.
2. **Collision-proof** — 2^122 possible values, collision probability negligible.
3. **Merge-safe** — multiple databases can generate IDs independently.
4. **Native PostgreSQL type** — stored as 16 bytes (vs 36 bytes for string representation).

### Tradeoffs

- Slightly worse index performance than sequential integers (mitigated: negligible for our scale).
- 16 bytes vs 4 bytes for integer PK (mitigated: acceptable storage overhead).
- No natural ordering (mitigated: use `created_at` for ordering).

### Future Impact

- UUIDv7 (time-ordered) could be adopted for better index locality when PostgreSQL 17+ is standard.
- IDs are safe for public API exposure — no enumeration attacks.
- Compatible with distributed databases (CockroachDB, Spanner) if we migrate.

---

## ADR-015: API Versioning

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

API changes must not break existing clients. We need a versioning strategy that allows evolution while maintaining backward compatibility.

### Chosen Solution

**URL path versioning (`/api/v1/`, `/api/v2/`)**

### Reason

1. **Explicit** — version is visible in every request, no ambiguity.
2. **Simple routing** — FastAPI router prefix handles it natively.
3. **Independent evolution** — v2 can have different DTOs, validation rules, even different handlers.
4. **Client-friendly** — frontend explicitly targets a version, no surprise breakage.

### Tradeoffs

- URL pollution (mitigated: only major versions get new prefixes).
- Code duplication between versions (mitigated: share domain/application layers, only duplicate presentation).
- More routes in NGINX config (mitigated: wildcard proxy rules).

### Future Impact

- When v2 is needed, v1 continues serving with a deprecation header.
- Mobile apps pinned to v1 won't break when web moves to v2.
- Sunset policy: deprecation warning → 6 months → removal.

---

## ADR-016: Avatar System

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

Users need visual identity. Custom uploads require file storage infrastructure. We need avatars without file upload complexity in Phase 1.

### Chosen Solution

**DiceBear generated avatars (Phase 1) → Custom uploads (Phase 2)**

### Reason

1. **Zero infrastructure** — DiceBear generates SVGs from a seed string (username/UUID).
2. **Deterministic** — same seed = same avatar. No storage needed.
3. **Customizable** — user can change style (bottts, avataaars, pixel-art, etc.) from Identity page.
4. **Instant** — no upload latency, no file processing.

### Tradeoffs

- Not personal photos (mitigated: Phase 2 adds custom uploads).
- Limited styles (mitigated: DiceBear has 20+ styles).
- External API dependency (mitigated: can self-host DiceBear or cache SVGs).

### Future Impact

- `avatar_seed` and `avatar_style` columns in users table enable regeneration.
- `avatar_url` column reserved for Phase 2 custom uploads.
- Storage abstraction layer (ADR-022) will handle file uploads.

---

## ADR-017: Error Handling Strategy

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

Errors must be handled consistently across all layers. Users should see friendly messages. Developers should see detailed context. Sensitive information must never leak.

### Chosen Solution

**Domain exceptions → Global exception handler → Structured error response**

### Architecture

```
Domain Layer:       raise DomainException("User not found", code="USER_NOT_FOUND")
Application Layer:  propagates exception (doesn't catch domain errors)
Presentation Layer: global exception handler catches and maps to HTTP response
Response:           { "error": { "code": "USER_NOT_FOUND", "message": "...", "correlation_id": "..." } }
```

### Reason

1. **Domain exceptions** carry business meaning, not HTTP status codes.
2. **Global handler** maps domain exceptions to HTTP responses — single mapping point.
3. **Correlation ID** in every error response — ties client error to server logs.
4. **Never expose stack traces** in production — only in development mode.

### Future Impact

- Error codes become a stable API contract — clients can programmatically handle specific errors.
- Error monitoring (Sentry, Bugsnag) integrates at the global handler level.
- Error rate metrics feed into health checks and alerting.

---

## ADR-018: Deployment Architecture

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

We need a deployment strategy that works locally (Docker Compose), in production (AWS), and is cloud-agnostic enough to migrate to any provider.

### Chosen Solution

**Docker Compose (dev) → AWS ECS or EC2 (prod) — cloud-agnostic containers**

### Reason

1. **Docker Compose locally** — one command starts the entire stack.
2. **Same containers in production** — identical behavior, no "works on my machine".
3. **Cloud-agnostic** — Docker containers run on AWS, GCP, Azure, Hetzner, DigitalOcean.
4. **AWS ECS** for production — managed container orchestration without Kubernetes complexity.
5. **Fallback to EC2** — simple Docker Compose on a single server for MVP launch.

### Tradeoffs

- AWS ECS has vendor-specific configuration (mitigated: Terraform abstracts this).
- Not Kubernetes (mitigated: ECS is simpler, K8s is overkill until we need multi-region).
- Single-region initially (mitigated: multi-region can be added with Route 53).

### Future Impact

- Kubernetes migration path exists via AWS EKS when scale demands it.
- Multi-region deployment via AWS Regions + Route 53 latency-based routing.
- Edge deployment (CloudFront for static assets) reduces latency globally.

---

## ADR-019: Rate Limiting Strategy

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

We need to prevent brute-force attacks on authentication, abuse of AI endpoints, and general API abuse — without affecting legitimate users.

### Chosen Solution

**Redis sliding window rate limiting with per-endpoint granularity**

### Rate Limits

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| Auth (login/register) | 5 requests | 15 minutes |
| AI Console (message) | 30 requests | 1 minute |
| General API | 100 requests | 1 minute |
| WebSocket connections | 5 per user | concurrent |
| Provider key validation | 3 requests | 1 minute |

### Reason

1. **Sliding window** — more accurate than fixed window, no burst at window boundaries.
2. **Redis-backed** — atomic operations prevent race conditions under concurrency.
3. **Per-endpoint** — auth gets stricter limits than general API.
4. **Per-user + per-IP** — authenticated users tracked by user ID, anonymous by IP.

### Future Impact

- Tiered rate limits based on user plan (free vs premium).
- Rate limit headers (`X-RateLimit-Remaining`, `X-RateLimit-Reset`) for client awareness.
- DDoS protection at NGINX level (connection limits, request rate) as first defense.

---

## ADR-020: Animation Libraries

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

We need animations at three levels: micro-interactions (hover, focus), component transitions (mount/unmount, layout), and cinematic sequences (landing page, 3D).

### Chosen Solution

**Three-tier approach: CSS → Framer Motion → GSAP**

| Level | Tool | Usage |
|-------|------|-------|
| Micro | CSS transitions/animations | Hover, focus, color changes |
| Component | Framer Motion | Mount/unmount, layout, drag, scroll |
| Cinematic | GSAP | Complex timelines, scroll-triggered sequences |

### Reason

1. **CSS first** — zero runtime cost for simple transitions.
2. **Framer Motion** — React-native, handles AnimatePresence (exit animations), layout animations.
3. **GSAP** — unmatched for complex choreography, timeline control, ScrollTrigger.
4. **Never overlap** — each tool has a clear boundary, never used on the same element.

### Tradeoffs

- Three animation systems to learn (mitigated: clear boundaries reduce confusion).
- Bundle size: Framer Motion ~30KB, GSAP ~25KB (mitigated: tree-shaking, code splitting).

### Future Impact

- GSAP ScrollTrigger for landing page storytelling.
- Framer Motion's `useMotionValue` for physics-based interactions.
- Three.js animations use its own system — kept separate from DOM animations.

---

## ADR-021: Event Bus Architecture

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

Modules need to communicate without direct coupling. A notification module shouldn't import from the AI module — it should react to events.

### Chosen Solution

**Redis Pub/Sub (Phase 1) with abstraction for future Kafka/RabbitMQ**

### Reason

1. **Redis already in the stack** — no additional service.
2. **Simple Pub/Sub** — perfect for low-volume events (notifications, status changes).
3. **Abstract interface** — `EventBus` interface in domain layer, `RedisEventBus` in infrastructure.
4. **Swap to Kafka** when we need persistent events, replay, and high throughput.

### Future Impact

- Kafka for device events, automation triggers, audit streams.
- Event sourcing capability when events are persisted.
- CQRS read model updates via event subscription.

---

## ADR-022: File Storage Abstraction

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

Phase 2 will need file uploads (avatars, documents). Voice processing may need temporary file storage. We need a storage abstraction now to avoid a rewrite later.

### Chosen Solution

**Storage interface (local filesystem in Phase 1, S3-compatible in Phase 2)**

### Reason

1. **Interface defined now** — `StorageService` in domain interfaces.
2. **Local implementation** — `LocalStorageService` writes to a mounted volume.
3. **S3 implementation** — `S3StorageService` added in Phase 2, zero changes to application layer.
4. **Path references** — database stores relative paths, not absolute URLs.

### Future Impact

- S3-compatible works with AWS S3, GCS, MinIO, Cloudflare R2.
- CDN integration via CloudFront/CloudFlare for public file URLs.
- Pre-signed URLs for secure, temporary file access.

---

## ADR-023: Request Tracing

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

When debugging production issues, we need to trace a single request through API → service → repository → AI provider → WebSocket response.

### Chosen Solution

**Correlation ID middleware (UUID per request)**

### Architecture

```
Client → Request → Middleware assigns X-Correlation-ID
                  → Bound to structlog context
                  → Passed to AI provider calls
                  → Included in WebSocket messages
                  → Included in error responses
                  → Logged in audit trail
```

### Reason

1. **Single ID traces entire request lifecycle** — from API entry to AI response to WebSocket delivery.
2. **No external dependency** — UUID generation + middleware, nothing else.
3. **Client can provide ID** — if `X-Correlation-ID` header is set, we use it (mobile app tracing).

### Future Impact

- OpenTelemetry spans can use correlation ID as trace ID.
- Distributed tracing across microservices when architecture evolves.
- Error reports to users include correlation ID for support tickets.

---

## ADR-024: Module Naming Convention

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

Generic names like "Dashboard", "Chat", "Settings" make YUGI-AI feel like every other SaaS app. The naming should reinforce the AI Operating System identity.

### Chosen Solution

| Generic | YUGI-AI | Rationale |
|---------|---------|-----------|
| Dashboard | **Neural Workspace** | Intelligence + productivity, implies the workspace thinks with you |
| Chat | **AI Console** | Terminal/command-center metaphor, power-user feel |
| Settings | **System Core** | OS-level configuration, not "preferences" |
| Notifications | **Event Center** | System events, logs, alerts — not social notifications |
| Profile | **Identity** | Personal identity within the OS, not a social profile |

### Reason

1. **Brand identity** — every interaction reinforces that this is an operating system, not a website.
2. **User psychology** — "AI Console" implies power; "Chat" implies casual.
3. **Consistency** — all names follow a two-word compound noun pattern.
4. **Extensibility** — future modules follow the same pattern: "Device Hub", "Automation Engine", "Agent Fleet".

### Future Impact

- URL paths use kebab-case: `/console`, `/system-core`, `/event-center`, `/identity`.
- API paths use the same naming: `/api/v1/console/`, `/api/v1/system-core/`.
- Documentation, error messages, and UI copy all use these terms consistently.

---

## ADR-025: Database ORM and Migrations

| Field | Value |
|-------|-------|
| **Status** | `ACCEPTED` |
| **Date** | 2026-07-15 |

### Problem

We need an ORM that supports async operations, works with PostgreSQL's advanced features (JSONB, UUID, arrays), and provides reliable schema migration management.

### Alternatives

| Option | Pros | Cons |
|--------|------|------|
| **SQLAlchemy 2.0 + Alembic** | Async support, mature, flexible ORM, auto-migrations | Verbose model definitions |
| **Tortoise ORM** | Django-like, async-first | Smaller community, fewer PostgreSQL features |
| **SQLModel** | Pydantic integration, less boilerplate | Limited features, backed by SQLAlchemy anyway |
| **Prisma (Python)** | Great DX, auto-migrations | Early stage, Node-first, limited async support |

### Chosen Solution

**SQLAlchemy 2.0 (async) + Alembic**

### Reason

1. **SQLAlchemy 2.0** — native async sessions via `asyncpg`, supports all PostgreSQL types natively.
2. **Alembic** — `alembic revision --autogenerate` detects model changes and generates migration scripts.
3. **Mapped columns** — type-safe, IDE-friendly column definitions.
4. **Relationship loading** — `selectinload`, `joinedload` for N+1 prevention.
5. **Mature** — 15+ years of production use, every edge case is documented.

### Tradeoffs

- More verbose than SQLModel or Tortoise (mitigated: we use it only in infrastructure layer).
- Alembic auto-generate isn't perfect — always review generated migrations.
- Async SQLAlchemy is newer — some patterns differ from sync SQLAlchemy.

### Future Impact

- Connection pooling via `asyncpg` pool — tunable for production load.
- Read replica routing — SQLAlchemy supports session-level database selection.
- Alembic migrations run in CI/CD pipeline before deployment.

---

> **This document is a living record. Every significant engineering decision must be added here before implementation.**
> Format: Copy an existing ADR, assign the next number, fill in all fields.
> Review: All new ADRs should be discussed before status changes to `ACCEPTED`.
