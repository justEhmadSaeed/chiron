from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket

from chiron_backend.common.models import AgentEvent


class RealtimeHub:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, event: AgentEvent) -> None:
        stale_connections: list[WebSocket] = []
        for connection in self._connections:
            try:
                await connection.send_json(event.model_dump(mode="json"))
            except Exception:
                stale_connections.append(connection)

        for connection in stale_connections:
            self.disconnect(connection)

    async def idle(self) -> None:
        await asyncio.sleep(15)


def ensure_realtime_hub(state: Any) -> RealtimeHub:
    hub = getattr(state, "realtime_hub", None)
    if isinstance(hub, RealtimeHub):
        return hub

    realtime_hub = RealtimeHub()
    state.realtime_hub = realtime_hub
    return realtime_hub
