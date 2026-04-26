# Chiron

This repository is structured as a production-oriented monorepo with a React/Vite frontend and a Python multi-agent backend. Turborepo orchestrates cross-package builds, contracts generation, type-checking, and parallel local development.

## Structure

```text
.
├── apps/
│   └── web/                     # React/Vite app
├── backend/                     # FastAPI API + agent workers + shared Python code
├── packages/
│   ├── contracts/               # OpenAPI artifact + generated TypeScript types
│   └── ui/                      # Optional shared React UI package
├── docs/                        # Architecture and operational docs
├── ops/                         # Observability and infrastructure config
├── .github/workflows/           # CI pipelines
├── docker-compose.yml           # Local multi-service stack
├── turbo.json                   # Build graph and task caching
└── package.json                 # Root workspace scripts
```

## Development

### Prerequisites

- Node.js 20+
- pnpm 10+
- Python 3.12+
- Docker Desktop or compatible engine

### Install

```bash
pnpm install
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-dev.txt
```

### Firebase Setup

Chiron requires a Firebase Realtime Database for storing experiments.

1. **Create Database**: Go to the Firebase Console, create a new project, and create a Realtime Database.
2. **Get Credentials**: In Project Settings > Service accounts, generate a new private key and save the `.json` file as `backend/firebase-credentials.json` (ensure this remains in `.gitignore`).
3. **Set Environment Variables**: Create a `backend/.env` file with:

```bash
FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
```
*(See `backend/.env.example` for alternative configuration options).*

### Run locally

```bash
pnpm dev
```

This starts:

- `apps/web` on `http://localhost:3000`
- `backend` API on `http://localhost:8000`
- `backend` worker process for agent execution

### Linting and formatting

```bash
pnpm lint
pnpm format
pnpm format:check
```

Repo defaults:

- `ESLint` handles TypeScript and React from [eslint.config.mjs](/Users/ehmadsaeed/repos/Chiron/eslint.config.mjs)
- `Prettier` formats frontend, shared packages, JSON, and Markdown from [.prettierrc.json](/Users/ehmadsaeed/repos/Chiron/.prettierrc.json)
- `Ruff` formats and lints Python from [backend/pyproject.toml](/Users/ehmadsaeed/repos/Chiron/backend/pyproject.toml)
- `VS Code` picks the right formatter automatically via [.vscode/settings.json](/Users/ehmadsaeed/repos/Chiron/.vscode/settings.json)

### Contracts generation

```bash
pnpm contracts:generate
```

The backend exports OpenAPI, and `packages/contracts` is the single TypeScript import surface for frontend API types.

## Runtime model

- Frontend uses REST for request/response and WebSocket for live agent activity.
- API handles authentication, session orchestration, persistence boundaries, and fan-out of realtime events.
- Workers execute agent flows independently and can scale horizontally without scaling the API.
- Redis is the default coordination layer for queueing and pub/sub in production; the scaffold uses an in-memory hub to keep local setup simple.

## Deployment

- Deploy `apps/web` separately on Vercel or as a container.
- Deploy `backend` API and worker as separate services from the same codebase and image family.
- Use Redis for queueing/pub-sub and Postgres for run metadata, audit trails, and resumability.
- Export telemetry via OpenTelemetry to a collector, then to your logging/metrics stack.

Additional detail lives in [docs/architecture.md](/Users/ehmadsaeed/repos/Chiron/docs/architecture.md).
