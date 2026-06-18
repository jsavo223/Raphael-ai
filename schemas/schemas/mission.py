from pydantic import BaseModel
from typing import Optional


class Mission(BaseModel):
    mission_id: str
    goal: str
    status: str
    created_at: str
    updated_at: Optional[str] = None