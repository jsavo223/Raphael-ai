import hashlib
import json

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
    ) -> Event:
        previous_hash = self.event_store.events[-1].hash if self.event_store.events else None
        timestamp = utc_now()

        event_data = {
            "event_id": new_id("evt"),
            "event_type": event_type,
            "mission_id": mission_id,
            "task_id": None,
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
    ):
        event = self._build_event(
            event_type=event_type,
            mission_id=mission_id,
            correlation_id=correlation_id,
            payload=payload,
        )
        self.event_store.append(event)
        return event

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

        plan = create_simple_plan(goal)

        self._record_event(
            event_type="MISSION_PLANNED",
            mission_id=mission_id,
            correlation_id=correlation_id,
            payload={"task_count": len(plan), "plan": plan},
        )

        results = self.executor.execute_plan(plan)

        mission.status = "completed"
        mission.updated_at = utc_now().isoformat()
        self.mission_store.update(mission)

        self._record_event(
            event_type="MISSION_COMPLETED",
            mission_id=mission_id,
            correlation_id=correlation_id,
            payload={"result_count": len(results), "results": results},
        )

        return {
            "mission_id": mission_id,
            "correlation_id": correlation_id,
            "goal": goal,
            "status": "completed",
            "plan": plan,
            "results": results,
        }
