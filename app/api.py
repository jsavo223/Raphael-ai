from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, validator

from services.auth import require_owner_api_key
from services.chat_service import ChatService
from services.control_core import ControlCore
from services.limits import (
    MAX_CHAT_MESSAGE_LENGTH,
    MAX_EVIDENCE_ITEM_LENGTH,
    MAX_EVIDENCE_ITEMS,
    MAX_MISSION_GOAL_LENGTH,
    MAX_TRAINING_DESCRIPTION_LENGTH,
    MAX_TRAINING_FIELD_LENGTH,
    MAX_TRAINING_REASON_LENGTH,
    MAX_TRAINING_TITLE_LENGTH,
)
from services.rate_limit import InMemoryRateLimiter, get_rate_limit_key


app = FastAPI(
    title="Raphael AI",
    version="0.1.0"
)

control_core = ControlCore()
chat_service = ChatService(control_core)
rate_limiter = InMemoryRateLimiter(max_requests=60, window_seconds=60)


def require_rate_limit(request: Request):
    rate_limiter.check(get_rate_limit_key(request))
    return True


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_CHAT_MESSAGE_LENGTH)


class MissionRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=MAX_MISSION_GOAL_LENGTH)


class TrainingSuggestionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=MAX_TRAINING_TITLE_LENGTH)
    description: str = Field(..., min_length=1, max_length=MAX_TRAINING_DESCRIPTION_LENGTH)
    target_agent: str = Field("general_agent", max_length=MAX_TRAINING_FIELD_LENGTH)
    category: str = Field("capability_improvement", max_length=MAX_TRAINING_FIELD_LENGTH)
    priority: str = Field("medium", max_length=MAX_TRAINING_FIELD_LENGTH)
    source_mission_id: Optional[str] = Field(default=None, max_length=MAX_TRAINING_FIELD_LENGTH)
    evidence: List[str] = Field(default_factory=list, max_length=MAX_EVIDENCE_ITEMS)

    @validator("evidence")
    def validate_evidence_items(cls, evidence):
        for item in evidence:
            if len(item) > MAX_EVIDENCE_ITEM_LENGTH:
                raise ValueError("Evidence item is too long.")
        return evidence


class TrainingDecisionRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=MAX_TRAINING_REASON_LENGTH)


class TrainingTestRequest(BaseModel):
    test_notes: Optional[str] = Field(default=None, max_length=MAX_TRAINING_DESCRIPTION_LENGTH)


@app.get("/")
def health():
    return {
        "status": "online",
        "service": "raphael-ai",
        "version": "0.1.0"
    }


@app.post("/chat")
def chat(
    request: ChatRequest,
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    return chat_service.handle_message(request.message)


@app.get("/health")
def detailed_health(
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    return {
        "status": "healthy",
        "mission_store": "connected",
        "event_store": "connected",
        "worker_pool": "connected",
        "training_agent": "connected",
        "chat_service": "connected",
        "rate_limiter": "connected"
    }


@app.post("/missions")
def create_mission(
    request: MissionRequest,
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    return control_core.create_mission(request.goal)


@app.get("/missions")
def list_missions(
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    return {
        "missions": control_core.mission_store.get_all()
    }


@app.get("/missions/{mission_id}/status")
def get_mission_status(
    mission_id: str,
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    progress = control_core.get_mission_progress(mission_id)

    if progress is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    return progress


@app.get("/missions/{mission_id}")
def get_mission(
    mission_id: str,
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    mission = control_core.mission_store.get(mission_id)

    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    return mission


@app.get("/missions/{mission_id}/events")
def get_mission_events(
    mission_id: str,
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    mission = control_core.mission_store.get(mission_id)

    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    return {
        "mission_id": mission_id,
        "events": control_core.event_store.get_by_mission(mission_id)
    }


@app.get("/training/suggestions")
def list_training_suggestions(
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    return {
        "suggestions": control_core.training_store.get_all()
    }


@app.post("/training/suggestions")
def create_training_suggestion(
    request: TrainingSuggestionRequest,
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    return control_core.create_training_suggestion(
        title=request.title,
        description=request.description,
        target_agent=request.target_agent,
        category=request.category,
        priority=request.priority,
        source_mission_id=request.source_mission_id,
        evidence=request.evidence,
    )


@app.get("/training/suggestions/{suggestion_id}")
def get_training_suggestion(
    suggestion_id: str,
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    suggestion = control_core.get_training_suggestion(suggestion_id)

    if suggestion is None:
        raise HTTPException(status_code=404, detail="Training suggestion not found")

    return suggestion


@app.post("/training/suggestions/{suggestion_id}/approve")
def approve_training_suggestion(
    suggestion_id: str,
    request: TrainingDecisionRequest,
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    suggestion = control_core.approve_training_suggestion(
        suggestion_id=suggestion_id,
        reason=request.reason,
    )

    if suggestion is None:
        raise HTTPException(status_code=404, detail="Training suggestion not found")

    return suggestion


@app.post("/training/suggestions/{suggestion_id}/reject")
def reject_training_suggestion(
    suggestion_id: str,
    request: TrainingDecisionRequest,
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    suggestion = control_core.reject_training_suggestion(
        suggestion_id=suggestion_id,
        reason=request.reason,
    )

    if suggestion is None:
        raise HTTPException(status_code=404, detail="Training suggestion not found")

    return suggestion


@app.post("/training/suggestions/{suggestion_id}/mark-tested")
def mark_training_suggestion_tested(
    suggestion_id: str,
    request: TrainingTestRequest,
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    suggestion = control_core.mark_training_suggestion_tested(
        suggestion_id=suggestion_id,
        test_notes=request.test_notes,
    )

    if suggestion is None:
        raise HTTPException(
            status_code=404,
            detail="Training suggestion not found or not ready for testing",
        )

    return suggestion


@app.post("/training/suggestions/{suggestion_id}/apply")
def apply_training_suggestion(
    suggestion_id: str,
    request: TrainingDecisionRequest,
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    suggestion = control_core.apply_training_suggestion(
        suggestion_id=suggestion_id,
        reason=request.reason,
    )

    if suggestion is None:
        raise HTTPException(
            status_code=404,
            detail="Training suggestion not found or not tested",
        )

    return suggestion


@app.post("/training/analyze-mission/{mission_id}")
def analyze_mission_for_training(
    mission_id: str,
    _rate_limit: bool = Depends(require_rate_limit),
    _owner: bool = Depends(require_owner_api_key),
):
    suggestions = control_core.analyze_mission_for_training(mission_id)

    if suggestions is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    return {
        "mission_id": mission_id,
        "suggestions": suggestions
    }
