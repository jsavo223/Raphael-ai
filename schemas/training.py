from typing import List, Optional

from pydantic import BaseModel, Field


class TrainingSuggestion(BaseModel):
    suggestion_id: str
    source_mission_id: Optional[str] = None
    target_agent: str
    category: str
    priority: str
    title: str
    description: str
    evidence: List[str] = Field(default_factory=list)
    status: str = "proposed"
    created_at: str
    approved_at: Optional[str] = None
    rejected_at: Optional[str] = None
    test_required_at: Optional[str] = None
    tested_at: Optional[str] = None
    test_notes: Optional[str] = None
    applied_at: Optional[str] = None
