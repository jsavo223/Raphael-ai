import hashlib
import json
from typing import Optional

from agents.training_agent import TrainingAgent
from core.ids import new_id
from core.time import utc_now
from schemas.event import Event
from schemas.mission import Mission
from services.event_store import EventStore
from services.executor import Executor
from services.mission_store import MissionStore
from services.plan_engine import create_simple_plan
from services.sandbox_policy import SandboxPolicy
from services.tool_registry import ToolRegistry
from services.training_store import TrainingStore


class ControlCore:
    def __init__(self):
        self.executor = Executor()
        self.event_store = EventStore()
        self.mission_store = MissionStore()
        self.training_store = TrainingStore()
        self.training_agent = TrainingAgent(self.training_store)
        self.tool_registry = ToolRegistry()
        self.sandbox_policy = SandboxPolicy()

    def _build_event(
        self,
        event_type: str,
        mission_id: str,
        correlation_id: str,
        payload: dict,
        task_id: Optional[str] = None,
    ) -> Event:
        previous_hash = self.event_store.events[-1].hash if self.event_store.events else None
        timestamp = utc_now()

        event_data = {
            "event_id": new_id("evt"),
            "event_type": event_type,
            "mission_id": mission_id,
            "task_id": task_id,
            "plan_id": None,
            "timestamp": timestamp.isoformat(),
            "actor_type": "control_core",
            "actor_id": "control_core_main",
            "correlation_id": correlation_id,
            "payload": payload,
            "previous_hash": previous_hash,
        }

        event_hash = hashlib.sha256(
            json.dumps(event_data, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        return Event(**event_data, hash=event_hash)

    def _record_event(
        self,
        event_type: str,
        mission_id: str,
        correlation_id: str,
        payload: dict,
        task_id: Optional[str] = None,
    ):
        event = self._build_event(
            event_type=event_type,
            mission_id=mission_id,
            correlation_id=correlation_id,
            payload=payload,
            task_id=task_id,
        )
        self.event_store.append(event)
        return event

    def _attach_task_metadata(self, plan, mission_id: str):
        for index, task in enumerate(plan):
            task["task_id"] = new_id("task")
            task["mission_id"] = mission_id
            task["sequence"] = index + 1
            task["status"] = "pending"
        return plan

    def validate_tool_request(
        self,
        tool_name: str,
        approved: bool = False,
        command: Optional[str] = None,
        file_path: Optional[str] = None,
    ):
        permission = self.tool_registry.require_allowed(tool_name, approved=approved)

        if tool_name == "terminal_command":
            if command is None:
                raise ValueError("terminal_command requires a command value.")
            self.sandbox_policy.validate_command(command, approved=approved)

        if tool_name in ("file_read", "file_write"):
            if file_path is None:
                raise ValueError(f"{tool_name} requires a file_path value.")
            self.sandbox_policy.validate_file_path(file_path, approved=approved)

        return permission

    def get_mission_progress(self, mission_id: str):
        mission = self.mission_store.get(mission_id)

        if mission is None:
            return None

        events = self.event_store.get_by_mission(mission_id)
        planned_events = [event for event in events if event.event_type == "MISSION_PLANNED"]
        latest_plan = planned_events[-1].payload.get("plan", []) if planned_events else []

        task_count = len(latest_plan)
        completed_task_ids = {
            event.task_id for event in events if event.event_type == "TASK_COMPLETED"
        }
        failed_task_ids = {
            event.task_id for event in events if event.event_type == "TASK_FAILED"
        }
        started_task_ids = {
            event.task_id for event in events if event.event_type == "TASK_STARTED"
        }

        finished_task_ids = completed_task_ids.union(failed_task_ids)
        running_task_ids = started_task_ids.difference(finished_task_ids)

        current_task = None
        for event in reversed(events):
            if event.event_type == "TASK_STARTED" and event.task_id in running_task_ids:
                current_task = {
                    "task_id": event.task_id,
                    "title": event.payload.get("title"),
                    "worker_type": event.payload.get("worker_type"),
                }
                break

        finished_count = len(finished_task_ids)
        progress_percentage = 100 if task_count == 0 and mission.status == "completed" else 0
        if task_count > 0:
            progress_percentage = round((finished_count / task_count) * 100, 2)

        last_event = events[-1] if events else None

        return {
            "mission_id": mission.mission_id,
            "goal": mission.goal,
            "status": mission.status,
            "task_count": task_count,
            "completed_task_count": len(completed_task_ids),
            "failed_task_count": len(failed_task_ids),
            "running_task_count": len(running_task_ids),
            "progress_percentage": progress_percentage,
            "current_task": current_task,
            "last_event_type": last_event.event_type if last_event else None,
            "last_updated_at": mission.updated_at,
        }

    def analyze_mission_for_training(self, mission_id: str):
        mission = self.mission_store.get(mission_id)

        if mission is None:
            return None

        events = self.event_store.get_by_mission(mission_id)
        return self.training_agent.analyze_mission(mission, events)

    def create_training_suggestion(
        self,
        title: str,
        description: str,
        target_agent: str = "general_agent",
        category: str = "capability_improvement",
        priority: str = "medium",
        source_mission_id: Optional[str] = None,
        evidence=None,
    ):
        return self.training_agent.create_suggestion(
            title=title,
            description=description,
            target_agent=target_agent,
            category=category,
            priority=priority,
            source_mission_id=source_mission_id,
            evidence=evidence or [],
        )

    def get_training_suggestion(self, suggestion_id: str):
        return self.training_store.get(suggestion_id)

    def approve_training_suggestion(self, suggestion_id: str, reason: Optional[str] = None):
        suggestion = self.training_store.get(suggestion_id)

        if suggestion is None:
            return None

        suggestion.status = "test_required"
        suggestion.approved_at = utc_now().isoformat()
        suggestion.test_required_at = utc_now().isoformat()
        suggestion.rejected_at = None

        if reason:
            suggestion.evidence.append(f"approval_reason={reason}")

        return self.training_store.update(suggestion)

    def reject_training_suggestion(self, suggestion_id: str, reason: Optional[str] = None):
        suggestion = self.training_store.get(suggestion_id)

        if suggestion is None:
            return None

        suggestion.status = "rejected"
        suggestion.rejected_at = utc_now().isoformat()

        if reason:
            suggestion.evidence.append(f"rejection_reason={reason}")

        return self.training_store.update(suggestion)

    def mark_training_suggestion_tested(
        self,
        suggestion_id: str,
        test_notes: Optional[str] = None,
    ):
        suggestion = self.training_store.get(suggestion_id)

        if suggestion is None:
            return None

        if suggestion.status not in ("test_required", "tested"):
            return None

        suggestion.status = "tested"
        suggestion.tested_at = utc_now().isoformat()
        suggestion.test_notes = test_notes

        return self.training_store.update(suggestion)

    def apply_training_suggestion(self, suggestion_id: str, reason: Optional[str] = None):
        suggestion = self.training_store.get(suggestion_id)

        if suggestion is None:
            return None

        if suggestion.status != "tested":
            return None

        suggestion.status = "applied"
        suggestion.applied_at = utc_now().isoformat()

        if reason:
            suggestion.evidence.append(f"apply_reason={reason}")

        return self.training_store.update(suggestion)

    def create_mission(self, goal: str):
        mission_id = new_id("mission")
        correlation_id = new_id("corr")
        created_at = utc_now().isoformat()

        mission = Mission(
            mission_id=mission_id,
            goal=goal,
            status="running",
            created_at=created_at,
        )
        self.mission_store.add(mission)

        self._record_event(
            event_type="MISSION_CREATED",
            mission_id=mission_id,
            correlation_id=correlation_id,
            payload={"goal": goal},
        )

        plan = self._attach_task_metadata(
            create_simple_plan(goal),
            mission_id=mission_id,
        )

        self._record_event(
            event_type="MISSION_PLANNED",
            mission_id=mission_id,
            correlation_id=correlation_id,
            payload={"task_count": len(plan), "plan": plan},
        )

        results = self.executor.execute_plan(
            plan,
            mission_id=mission_id,
            correlation_id=correlation_id,
            event_callback=self._record_event,
        )

        mission_failed = any(result.get("status") == "failed" for result in results)
        final_status = "failed" if mission_failed else "completed"

        mission.status = final_status
        mission.updated_at = utc_now().isoformat()
        self.mission_store.update(mission)

        self._record_event(
            event_type="MISSION_FAILED" if mission_failed else "MISSION_COMPLETED",
            mission_id=mission_id,
            correlation_id=correlation_id,
            payload={"result_count": len(results), "results": results},
        )

        return {
            "mission_id": mission_id,
            "correlation_id": correlation_id,
            "goal": goal,
            "status": final_status,
            "plan": plan,
            "results": results,
        }
