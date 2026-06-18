import hashlib
import json
from typing import Optional

from core.ids import new_id
from core.time import utc_now
from schemas.event import Event
from schemas.mission import Mission
from services.event_store import EventStore
from services.executor import Executor
from services.mission_store import MissionStore
from services.plan_engine import create_simple_plan


class ControlCore:
    def __init__(self):
        self.executor = Executor()
        self.event_store = EventStore()
        self.mission_store = MissionStore()

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
