from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class Event(BaseModel):
    event_id: str
    event_type: str

    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    plan_id: Optional[str] = None

    timestamp: datetime

    actor_type: str
    actor_id: str

    correlation_id: str

    payload: Dict[str, Any]

    hash: str
    previous_hash: Optional[str] = None