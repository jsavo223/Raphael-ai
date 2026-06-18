from typing import Any, List, Optional

from pydantic import BaseModel


class Task(BaseModel):
    task_id: str
    mission_id: str
    title: str
    description: str
    worker_type: str
    dependencies: List[str]
    status: str = "pending"
    output: Optional[Any] = None
    error: Optional[str] = None
