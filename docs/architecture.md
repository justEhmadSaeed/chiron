# Architecture

## Design goals

- Independent deployability for web, API, and workers
- Shared contracts without duplicating model definitions
- Fast local iteration with hot reload on both stacks
- Clear path from simple local dev to horizontally scaled production

## Folder layout

```text
apps/
  web/
    src/app/                     # React components and routing
    src/components/              # Web app components
    src/lib/api/                 # Backend REST client
    src/lib/realtime/            # WebSocket/SSE client logic
backend/
  src/chiron_backend/
    api/                         # FastAPI entrypoints and routers
    agents/                      # Worker runtime and agent orchestration
    common/                      # Settings, logging, shared models
  scripts/                       # OpenAPI and ops scripts
  tests/unit/                    # Fast unit tests
  tests/integration/             # API integration tests
packages/
  contracts/                     # Generated TS types from backend OpenAPI
  ui/                            # Optional shared React components
ops/
  otel/                          # Collector config
```

## Communication pattern

- `REST`: create runs, fetch run state, fetch audit trails, manage sessions
- `WebSocket`: push agent lifecycle events to the browser
- `Redis`: queue jobs and distribute worker events across API instances
- `Postgres`: durable run state, messages, tool traces, and analytics

For local development, the scaffold uses an in-memory broadcaster so the API remains easy to boot without infrastructure. Production should replace that adapter with Redis pub/sub or a durable event bus.

## Scaling model

- `web`: stateless horizontal scale behind CDN/edge
- `api`: stateless horizontal scale behind load balancer
- `worker`: independent autoscaling by queue depth, model latency, or tenant partition
- `redis`: shared queue and pub/sub backbone
- `postgres`: durable system of record

## Observability

- Structured JSON logs from API and worker
- OpenTelemetry instrumentation for request traces and worker spans
- Correlation IDs carried from frontend request to agent execution events
- Metrics to track queue depth, run latency, token usage, and tool failures

## Testing strategy

- `frontend unit`: React component and API client tests
- `backend unit`: model validation, orchestration, and helpers
- `integration`: FastAPI routes, websocket flows, and worker enqueue paths
- `e2e`: full browser-to-agent scenario against docker-compose stack

## Deployment patterns

### Recommended

- `apps/web`: Vercel
- `backend/api`: container platform such as ECS, Fly.io, Cloud Run, or Kubernetes
- `backend/worker`: separate worker deployment on the same platform
- `redis` and `postgres`: managed services

### Combined container

Useful for demos or very small environments, but not recommended for production because API and worker scaling characteristics diverge quickly.
