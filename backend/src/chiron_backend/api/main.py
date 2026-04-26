from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from chiron_backend.api.routes.agents import router as agents_router
from chiron_backend.api.routes.experiments import router as experiments_router
from chiron_backend.api.routes.health import router as health_router
from chiron_backend.common.firebase import initialize_firebase
from chiron_backend.common.logging import configure_logging
from chiron_backend.common.realtime import RealtimeHub, ensure_realtime_hub


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    initialize_firebase()
    app.state.realtime_hub = RealtimeHub()
    yield


app = FastAPI(
    title="Chiron API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(agents_router)
app.include_router(experiments_router)


@app.websocket("/ws/agent-events")
async def websocket_agent_events(websocket: WebSocket) -> None:
    hub: RealtimeHub = ensure_realtime_hub(app.state)
    await hub.connect(websocket)
    try:
        while True:
            await hub.idle()
    except WebSocketDisconnect:
        hub.disconnect(websocket)
