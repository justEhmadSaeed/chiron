import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from firebase_admin import db

from datetime import datetime
from chiron_backend.common.models import ExperimentCreateRequest, ExperimentResponse, ExperimentStatus, utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


@router.post("/generate", response_model=ExperimentResponse)
async def generate_experiment(request: ExperimentCreateRequest) -> ExperimentResponse:
    try:
        experiment_id = str(uuid4())
        created_at_str = utc_now().isoformat()

        experiment_data = {
            "question": request.question,
            "status": ExperimentStatus.RUNNING.value,
            "createdAt": created_at_str
        }

        # Save to Firebase Realtime Database
        ref = db.reference("experiments")
        ref.child(experiment_id).set(experiment_data)

        return ExperimentResponse(
            experiment_id=experiment_id,
            question=request.question,
            status=ExperimentStatus.RUNNING,
            created_at=created_at_str
        )
    except Exception as e:
        logger.error(f"Failed to generate experiment in Firebase: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while creating experiment")


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(experiment_id: str) -> ExperimentResponse:
    try:
        ref = db.reference(f"experiments/{experiment_id}")
        data = ref.get()

        if not data:
            raise HTTPException(status_code=404, detail="Experiment not found")

        current_status = data.get("status", ExperimentStatus.RUNNING.value)
        created_at_str = data.get("createdAt")
        plan_started_at_str = data.get("planStartedAt")

        # Simulated progression logic
        now = utc_now()
        updated = False

        if current_status == ExperimentStatus.RUNNING.value and created_at_str:
            created_at = datetime.fromisoformat(created_at_str)
            if (now - created_at).total_seconds() > 5:
                current_status = ExperimentStatus.LQC_COMPLETED.value
                data["status"] = current_status
                updated = True

        if current_status == ExperimentStatus.PLANNING.value and plan_started_at_str:
            plan_started_at = datetime.fromisoformat(plan_started_at_str)
            if (now - plan_started_at).total_seconds() > 5:
                current_status = ExperimentStatus.COMPLETED.value
                data["status"] = current_status
                updated = True

        if updated:
            ref.update({"status": current_status})

        return ExperimentResponse(
            experiment_id=experiment_id,
            question=data.get("question", ""),
            status=ExperimentStatus(current_status),
            created_at=created_at_str or now.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch experiment {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching experiment")


@router.post("/{experiment_id}/start-plan", response_model=ExperimentResponse)
async def start_plan(experiment_id: str) -> ExperimentResponse:
    try:
        ref = db.reference(f"experiments/{experiment_id}")
        data = ref.get()

        if not data:
            raise HTTPException(status_code=404, detail="Experiment not found")

        plan_started_at_str = utc_now().isoformat()
        current_status = ExperimentStatus.PLANNING.value
        
        ref.update({
            "status": current_status,
            "planStartedAt": plan_started_at_str
        })

        return ExperimentResponse(
            experiment_id=experiment_id,
            question=data.get("question", ""),
            status=ExperimentStatus(current_status),
            created_at=data.get("createdAt", plan_started_at_str)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start plan for experiment {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while starting plan")
