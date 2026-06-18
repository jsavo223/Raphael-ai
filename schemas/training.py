from typing import List, Optional

from pydantic import BaseModel


class TrainingSuggestion(BaseModel):
    suggestion_id: str
    source_mission_id: Optional[str] = None
    target_agent: str
    category: str
    priority: str
    title: str
    description: str
    evidence: List[str] = []
    status: str = "proposed"
    created_at: str
    approved_at: Optional[str] = None
    applied_at: Optional[str] = None
