import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from firebase_admin import db

from chiron_backend.agents.research.experiment_pipeline import run_experiment_pipeline
from chiron_backend.common.models import (
    AgentEvent,
    ExperimentCreateRequest,
    ExperimentFeedback,
    ExperimentResponse,
    ExperimentStatus,
    utc_now,
)
from chiron_backend.common.realtime import ensure_realtime_hub

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


async def simulate_lqc_process(experiment_id: str, hub: Any) -> None:
    """
    Runs the real adversarial validation pipeline for the given experiment,
    writes the QC result to Firebase, and broadcasts LQC_COMPLETED.
    """
    try:
        ref = db.reference(f"experiments/{experiment_id}")
        data = ref.get() or {}
        hypothesis = data.get("question", "")

        if not hypothesis:
            logger.error(f"[LQC] No hypothesis found for experiment {experiment_id}")
            return

        logger.info(f"[LQC] Running adversarial pipeline for experiment {experiment_id}")

        from chiron_backend.agents.research.graph import build_graph

        graph = build_graph()
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(
                pool,
                lambda: graph.invoke({
                    "research_prompt": hypothesis,
                    "experiment_id": experiment_id,
                }),
            )

        from chiron_backend.common.models import QCResult
        qc_dict = json.loads(result.get("final_client_report", "{}"))
        qc_result = QCResult.model_validate(qc_dict)
        qc_to_save = qc_result.model_dump()
        logger.info(f"[LQC] Saving QCResult — signal={qc_to_save.get('signal')}, "
                    f"noveltyScore={qc_to_save.get('noveltyScore')}, "
                    f"references={len(qc_to_save.get('references', []))}")
        ref.update({"status": ExperimentStatus.LQC_COMPLETED.value, "LQC": qc_to_save})


        event = AgentEvent(
            run_id=experiment_id,
            event_type="LQC_COMPLETED",
            payload={
                "experiment_id": experiment_id,
                "status": ExperimentStatus.LQC_COMPLETED.value,
            },
        )
        await hub.broadcast(event)
        logger.info(f"[LQC] Broadcasted LQC_COMPLETED for {experiment_id}")

    except Exception as e:
        logger.error(f"[LQC] Error in lqc_process for {experiment_id}: {e}")


async def simulate_planning_process(experiment_id: str, hub: Any) -> None:
    """
    Runs the real experiment design pipeline for the given experiment,
    writes the plan to Firebase, and broadcasts PLAN_COMPLETED.
    """
    try:
        ref = db.reference(f"experiments/{experiment_id}")
        data = ref.get() or {}
        hypothesis = data.get("question", "")

        if not hypothesis:
            logger.error(f"[Plan] No hypothesis found for experiment {experiment_id}")
            return

        logger.info(f"[Plan] Running experiment design pipeline for experiment {experiment_id}")

        

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            plan_dict = await loop.run_in_executor(
                pool,
                lambda: run_experiment_pipeline(hypothesis),
            )

        ref.update({"status": ExperimentStatus.COMPLETED.value, "plan": plan_dict})

        event = AgentEvent(
            run_id=experiment_id,
            event_type="PLAN_COMPLETED",
            payload={"experiment_id": experiment_id, "status": ExperimentStatus.COMPLETED.value},
        )
        await hub.broadcast(event)
        logger.info(f"[Plan] Broadcasted PLAN_COMPLETED for {experiment_id}")

    except Exception as e:
        logger.error(f"[Plan] Error in planning_process for {experiment_id}: {e}")


@router.post("/generate", response_model=ExperimentResponse)
async def generate_experiment(
    request_data: ExperimentCreateRequest, background_tasks: BackgroundTasks, request: Request
) -> ExperimentResponse:
    try:
        experiment_id = str(uuid4())
        created_at_str = utc_now().isoformat()

        experiment_data = {
            "question": request_data.question,
            "status": ExperimentStatus.RUNNING.value,
            "createdAt": created_at_str,
        }

        # Save to Firebase Realtime Database
        ref = db.reference("experiments")
        ref.child(experiment_id).set(experiment_data)

        # Start simulation background task
        hub = ensure_realtime_hub(request.app.state)
        background_tasks.add_task(simulate_lqc_process, experiment_id, hub)

        return ExperimentResponse(
            experiment_id=experiment_id,
            question=request_data.question,
            status=ExperimentStatus.RUNNING,
            created_at=created_at_str,
        )
    except Exception as e:
        logger.error(f"Failed to generate experiment in Firebase: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while creating experiment"
        ) from e


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(experiment_id: str) -> ExperimentResponse:
    try:
        ref = db.reference(f"experiments/{experiment_id}")
        data = ref.get()

        if not data:
            raise HTTPException(status_code=404, detail="Experiment not found")

        current_status = data.get("status", ExperimentStatus.RUNNING.value)
        created_at_str = data.get("createdAt")

        return ExperimentResponse(
            experiment_id=experiment_id,
            question=data.get("question", ""),
            status=ExperimentStatus(current_status),
            created_at=created_at_str or utc_now().isoformat(),
            LQC=data.get("LQC"),
            plan=data.get("plan"),
            feedback=data.get("feedback"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch experiment {experiment_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching experiment"
        ) from e


@router.post("/{experiment_id}/start-plan", response_model=ExperimentResponse)
async def start_plan(
    experiment_id: str, background_tasks: BackgroundTasks, request: Request
) -> ExperimentResponse:
    try:
        ref = db.reference(f"experiments/{experiment_id}")
        data = ref.get()

        if not data:
            raise HTTPException(status_code=404, detail="Experiment not found")

        plan_started_at_str = utc_now().isoformat()
        current_status = ExperimentStatus.PLANNING.value

        ref.update({"status": current_status, "planStartedAt": plan_started_at_str})

        # Start simulation background task
        hub = ensure_realtime_hub(request.app.state)
        background_tasks.add_task(simulate_planning_process, experiment_id, hub)

        return ExperimentResponse(
            experiment_id=experiment_id,
            question=data.get("question", ""),
            status=ExperimentStatus(current_status),
            created_at=data.get("createdAt", plan_started_at_str),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start plan for experiment {experiment_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while starting plan"
        ) from e


@router.post("/{experiment_id}/feedback", response_model=ExperimentResponse)
async def submit_experiment_feedback(
    experiment_id: str,
    feedback: ExperimentFeedback,
) -> ExperimentResponse:
    try:
        ref = db.reference(f"experiments/{experiment_id}")
        data = ref.get()

        if not data:
            raise HTTPException(status_code=404, detail="Experiment not found")

        ref.child("feedback").set({k: v.model_dump() for k, v in feedback.items()})

        updated_data = ref.get()
        current_status = updated_data.get("status", ExperimentStatus.RUNNING.value)

        return ExperimentResponse(
            experiment_id=experiment_id,
            question=updated_data.get("question", ""),
            status=ExperimentStatus(current_status),
            created_at=updated_data.get("createdAt") or utc_now().isoformat(),
            LQC=updated_data.get("LQC"),
            plan=updated_data.get("plan"),
            feedback=updated_data.get("feedback"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback for experiment {experiment_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while submitting feedback"
        ) from e
