import pytest
from fastapi import HTTPException

from agents.training_agent import TrainingAgent
from services.chat_service import ChatService
from services.control_core import ControlCore
from services.event_store import EventStore
from services.mission_store import MissionStore
from services.rate_limit import InMemoryRateLimiter
from services.training_store import TrainingStore


def build_test_control_core(tmp_path):
    control_core = ControlCore()
    control_core.event_store = EventStore(str(tmp_path / "events.json"))
    control_core.mission_store = MissionStore(str(tmp_path / "missions.json"))
    control_core.training_store = TrainingStore(str(tmp_path / "training_suggestions.json"))
    control_core.training_agent = TrainingAgent(control_core.training_store)
    return control_core


def test_mission_flow_records_progress_and_events(tmp_path):
    control_core = build_test_control_core(tmp_path)

    result = control_core.create_mission("Build a simple test app")
    mission_id = result["mission_id"]

    assert result["status"] == "completed"
    assert mission_id

    mission = control_core.mission_store.get(mission_id)
    assert mission is not None
    assert mission.status == "completed"

    events = control_core.event_store.get_by_mission(mission_id)
    event_types = [event.event_type for event in events]

    assert "MISSION_CREATED" in event_types
    assert "MISSION_PLANNED" in event_types
    assert "TASK_STARTED" in event_types
    assert "TASK_COMPLETED" in event_types
    assert "MISSION_COMPLETED" in event_types

    progress = control_core.get_mission_progress(mission_id)
    assert progress["status"] == "completed"
    assert progress["task_count"] == 3
    assert progress["completed_task_count"] == 3
    assert progress["failed_task_count"] == 0
    assert progress["progress_percentage"] == 100


def test_training_suggestion_requires_testing_before_apply(tmp_path):
    control_core = build_test_control_core(tmp_path)

    suggestion = control_core.create_training_suggestion(
        title="Improve app builder planning",
        description="Capture reusable planning steps for app and website projects.",
        target_agent="app_builder_agent",
        category="app_building_training",
        priority="medium",
        evidence=["completed_task_count=3"],
    )

    apply_before_testing = control_core.apply_training_suggestion(
        suggestion.suggestion_id,
        reason="Should not apply before testing.",
    )
    assert apply_before_testing is None

    approved = control_core.approve_training_suggestion(
        suggestion.suggestion_id,
        reason="Looks useful.",
    )
    assert approved.status == "test_required"

    tested = control_core.mark_training_suggestion_tested(
        suggestion.suggestion_id,
        test_notes="Passed dry-run review.",
    )
    assert tested.status == "tested"
    assert tested.tested_at is not None

    applied = control_core.apply_training_suggestion(
        suggestion.suggestion_id,
        reason="Test gate passed.",
    )
    assert applied.status == "applied"
    assert applied.applied_at is not None


def test_redaction_protects_stored_mission_goal(tmp_path):
    control_core = build_test_control_core(tmp_path)

    result = control_core.create_mission("Use api_key=super-secret-value to build an app")
    mission = control_core.mission_store.get(result["mission_id"])

    assert "super-secret-value" not in mission.goal
    assert "[REDACTED]" in mission.goal


def test_chat_service_returns_simple_user_facing_response(tmp_path):
    control_core = build_test_control_core(tmp_path)
    chat_service = ChatService(control_core)

    response = chat_service.handle_message("Build a simple landing page")

    assert response["mission_id"]
    assert response["status"] == "completed"
    assert response["progress"]["progress_percentage"] == 100
    assert response["next_action"] == "review_result"
    assert "reply" in response
    assert "completed" in response["reply"]


def test_rate_limiter_blocks_excess_requests():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)

    limiter.check("test-client")
    limiter.check("test-client")

    with pytest.raises(HTTPException) as error:
        limiter.check("test-client")

    assert error.value.status_code == 429
