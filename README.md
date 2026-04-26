<div align="center">
  <img src="https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/beaker.svg" width="80" height="80" alt="Chiron Logo" />
  <h1>CHIRON</h1>
  <p><b>The Autonomous Scientific Research Orchestrator</b></p>

  <p>
    <img src="https://img.shields.io/badge/version-1.0.0-cyan.svg?style=for-the-badge" alt="Version" />
    <img src="https://img.shields.io/badge/engine-Turborepo-ef4444.svg?style=for-the-badge&logo=turborepo" alt="Engine" />
    <img src="https://img.shields.io/badge/backend-FastAPI-05998b.svg?style=for-the-badge&logo=fastapi" alt="Backend" />
    <img src="https://img.shields.io/badge/frontend-React-61dafb.svg?style=for-the-badge&logo=react" alt="Frontend" />
  </p>

  <p align="center">
    <i>Accelerating scientific discovery through adversarial literature review and autonomous experimental design.</i>
  </p>
</div>

---

## 🧬 Overview

Chiron is an end-to-end, multi-agent platform designed to revolutionize scientific workflows. It rigorously validates hypothesis novelty through an **adversarial literature review** process. Once a hypothesis is verified, Chiron dynamically generates comprehensive experimental plans using a **continuous-learning RAG architecture** that adapts based on expert feedback.

### Key Pillars
- **Adversarial Validation**: Multi-agent review system to stress-test hypothesis novelty.
- **Dynamic Orchestration**: Automated generation of multi-week experimental protocols.
- **Continuous Learning**: Real-time feedback loop to refine protocol accuracy without retraining.
- **Typed Integration**: Unified contract surface between FastAPI and React/Vite.

---

## 🏗️ Project Architecture

Chiron is built as a high-performance monorepo using **Turborepo** and **pnpm**.

<details>
<summary><b>View Repository Map</b></summary>

```text
.
├── apps/
│   └── web/                     # Next-gen React/Vite Frontend
├── backend/                     # FastAPI API + Distributed Agent Workers
├── packages/
│   ├── contracts/               # OpenAPI Contract Surface (Shared Types)
│   └── ui/                      # Shared Tailwind UI Primitives
├── docs/                        # Architecture & Implementation Guides
├── ops/                         # Infrastructure & Observability (OTel)
├── turbo.json                   # Build Graph & Cache Management
└── docker-compose.yml           # Production-ready Local Stack
```
</details>

---

## 🚀 Getting Started

### Prerequisites
- **Node.js** 20+ & **pnpm** 10+
- **Python** 3.12+
- **Docker** Desktop or compatible engine

### Quick Installation

```bash
# 1. Install dependencies
pnpm install

# 2. Setup Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-dev.txt
```

### Infrastructure Setup
Chiron leverages Firebase for real-time data persistence.

1. **Initialize Firebase**: Create a Realtime Database in the [Firebase Console](https://console.firebase.google.com/).
2. **Credentials**: Save your service account key to `backend/firebase-credentials.json`.
3. **Environment**: Configure your `backend/.env`:
   ```bash
   FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com
   FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
   ```

---

## 🛠️ Development Workflow

Run the entire stack in parallel with a single command:

```bash
pnpm dev
```

| Service | Endpoint | Responsibility |
| :--- | :--- | :--- |
| **Web App** | `localhost:3000` | Research Dashboard & Visualization |
| **API** | `localhost:8000` | Session Orchestration & Persistence |
| **Workers** | Background | Distributed Agent Execution |

### Quality Standards
Maintain the integrity of the scientific engine with our unified toolchain:

- **Linting**: `pnpm lint` (ESLint + Ruff)
- **Formatting**: `pnpm format` (Prettier + Ruff)
- **Type Safety**: `pnpm typecheck` (tsc + mypy)
- **Contracts**: `pnpm contracts:generate` (OpenAPI to TS)

---

## 📡 Runtime & Deployment

### Scalable Model
- **Real-time**: WebSocket-driven agent visibility.
- **Decoupled**: API and Workers scale independently via Redis.
- **Observable**: Full OpenTelemetry integration for audit trails.

### Deployment Strategy
- **Web**: Vercel or Containerized CDN.
- **Backend**: Scalable service mesh (API + Worker pool).
- **Persistence**: Redis (Pub/Sub) + Postgres (Metadata) + Firebase (Real-time).

---

<div align="center">
  <p>For deep technical dives, visit the <a href="./docs/architecture.md">Architecture Guide</a>.</p>
  <p>Built with ❤️ by the Chiron Team</p>
</div>
