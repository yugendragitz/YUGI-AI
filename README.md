# YUGI-AI

> **The AI Operating System** — Not a chatbot. Not a website. An intelligent operating system.

[![CI](https://github.com/yugendragitz/YUGI-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/yugendragitz/YUGI-AI/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB.svg)](https://python.org)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-000000.svg)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)](https://typescriptlang.org)

---

## Overview

YUGI-AI is a modular AI Operating System designed to connect with computers, mobile devices, networks, cloud services, AI models, and future robotics. Every feature behaves like an installable OS module — pluggable, replaceable, and independently scalable.

### Core Modules

| Module | Description |
|--------|-------------|
| **Neural Workspace** | Intelligent dashboard — system metrics, activity feed, quick actions |
| **AI Console** | Streaming AI conversations with multi-provider support |
| **System Core** | OS-level configuration — providers, models, voice, appearance |
| **Event Center** | Real-time system events, alerts, and notifications |
| **Identity** | User profile, avatar, and session management |

### Architecture Highlights

- **Clean Architecture** — Domain → Application → Infrastructure → Presentation
- **BYOK (Bring Your Own Key)** — Users provide their own AI API keys, encrypted at rest
- **Provider-Agnostic AI** — OpenAI, Claude, Gemini, OpenRouter, Ollama, LM Studio
- **Real-Time Streaming** — WebSocket-based AI response streaming
- **Voice Abstraction** — Swappable speech providers (Web Speech API, ElevenLabs, Azure)

---

## Tech Stack

### Frontend

| Technology | Purpose |
|-----------|---------|
| Next.js 15 (App Router) | Framework, SSR, routing |
| React 19 | UI components |
| TypeScript | Type safety |
| TailwindCSS v4 | Styling |
| Framer Motion | Component animations |
| GSAP | Complex choreography |
| Three.js + React Three Fiber | 3D effects |
| Zustand | Client state management |
| TanStack Query | Server state management |

### Backend

| Technology | Purpose |
|-----------|---------|
| FastAPI | REST API + WebSocket |
| Python 3.12+ | Runtime |
| Socket.IO | Real-time communication |
| SQLAlchemy 2.0 (async) | ORM |
| Alembic | Database migrations |
| PostgreSQL 16 | Primary database |
| Redis 7 | Cache, sessions, Pub/Sub |
| structlog | Structured logging |

### Infrastructure

| Technology | Purpose |
|-----------|---------|
| Docker Compose | Container orchestration |
| NGINX | Reverse proxy, SSL, rate limiting |
| GitHub Actions | CI/CD pipeline |

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) ≥ 24.0
- [Docker Compose](https://docs.docker.com/compose/install/) ≥ 2.20
- [Git](https://git-scm.com/) ≥ 2.40

### 1. Clone & Configure

```bash
git clone https://github.com/yugendragitz/YUGI-AI.git
cd YUGI-AI

# Create environment file from template
cp .env.example .env

# Generate secrets (run these and paste into .env)
openssl rand -hex 64                    # → SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # → ENCRYPTION_KEY
```

### 2. Start Development Stack

```bash
# Start all services with hot reload
docker compose -f docker-compose.dev.yml up --build

# Services will be available at:
#   Frontend:  http://localhost:3000
#   Backend:   http://localhost:8000
#   API Docs:  http://localhost:8000/docs
#   PostgreSQL: localhost:5432
#   Redis:      localhost:6379
```

### 3. Start Production Stack

```bash
# Build and start production services
docker compose up --build -d

# Application available at:
#   http://localhost (via NGINX)
```

---

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest --cov=app --cov-report=term-missing

# Lint
ruff check .
ruff format .

# Type check
mypy app/
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Lint
npm run lint

# Type check
npx tsc --noEmit
```

---

## Project Structure

```
YUGI-AI/
├── frontend/                 # Next.js 15 application
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   ├── components/      # Shared UI components
│   │   ├── features/        # Feature modules
│   │   ├── lib/             # Core utilities
│   │   └── providers/       # React context providers
│   └── Dockerfile
│
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/             # Presentation layer (routes)
│   │   ├── application/     # Use cases & services
│   │   ├── domain/          # Business logic & interfaces
│   │   ├── infrastructure/  # External implementations
│   │   └── core/            # Cross-cutting concerns
│   ├── alembic/             # Database migrations
│   └── Dockerfile
│
├── nginx/                    # Reverse proxy configs
├── scripts/                  # Utility scripts
├── docs/                     # Architecture documentation
│   ├── DESIGN_SYSTEM.md     # Visual design system
│   └── ARCHITECTURE_DECISIONS.md
│
├── docker-compose.yml        # Production orchestration
├── docker-compose.dev.yml    # Development orchestration
└── .github/workflows/        # CI/CD pipelines
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Design System](docs/DESIGN_SYSTEM.md) | Typography, colors, spacing, animations, glassmorphism, 3D, accessibility |
| [Architecture Decisions](docs/ARCHITECTURE_DECISIONS.md) | Every engineering decision with rationale and tradeoffs |

---

## Environment Variables

See [.env.example](.env.example) for the complete list of environment variables with documentation.

---

## Contributing

1. Follow the [Design System](docs/DESIGN_SYSTEM.md) for all UI changes.
2. Document architectural decisions in [ARCHITECTURE_DECISIONS.md](docs/ARCHITECTURE_DECISIONS.md).
3. Write tests for all new features.
4. Run `ruff check` and `ruff format` before committing Python code.
5. Run `npm run lint` before committing TypeScript code.

---

## License

[MIT](LICENSE) — See LICENSE file for details.

---

<p align="center">
  <strong>YUGI-AI</strong> — The future of intelligent computing.
</p>
