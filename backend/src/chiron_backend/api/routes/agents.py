from chiron_backend.api.store import RUNS
from chiron_backend.common.models import (
    AgentEvent,
    AgentRun,
    AgentRunCreateRequest,
    AgentRunStatus,
)
from chiron_backend.common.realtime import ensure_realtime_hub
from fastapi import APIRouter, Request

router = APIRouter(prefix="/v1/agent-runs", tags=["agent-runs"])


@router.get("", response_model=list[AgentRun])
async def list_agent_runs() -> list[AgentRun]:
    return RUNS


@router.post("", response_model=AgentRun)
async def create_agent_run(payload: AgentRunCreateRequest, request: Request) -> AgentRun:
    run = AgentRun(agent_name=payload.agent_name, status=AgentRunStatus.QUEUED)
    RUNS.append(run)

    hub = ensure_realtime_hub(request.app.state)
    await hub.broadcast(
        AgentEvent(
            run_id=run.run_id,
            event_type="run.queued",
            payload={"agent_name": run.agent_name, "input": payload.input},
        )
    )
    return run
