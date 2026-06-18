from typing import Any, Dict, List, Optional

from core.ids import new_id
from core.time import utc_now
from services.redaction import redact_data
from services.safe_json import SafeJsonStore


class ToolAuditLog:
    """
    Append-only audit log for tool access attempts.

    This records allowed and denied tool requests so future terminal, file,
    browser, email, calendar, and deployment actions can be reviewed.
    """

    def __init__(self, path: str = "data/tool_audit.json"):
        self.json_store = SafeJsonStore(path, default_value=[])
        self.records: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        return self.json_store.load()

    def _save(self):
        self.json_store.save([redact_data(record) for record in self.records])

    def record(
        self,
        tool_name: str,
        allowed: bool,
        reason: str,
        actor_type: str = "control_core",
        actor_id: str = "control_core_main",
        mission_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        record = {
            "audit_id": new_id("tool_audit"),
            "timestamp": utc_now().isoformat(),
            "tool_name": tool_name,
            "allowed": allowed,
            "reason": reason,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "mission_id": mission_id,
            "task_id": task_id,
            "metadata": redact_data(metadata or {}),
        }
        self.records.append(record)
        self._save()
        return record

    def get_all(self):
        return self.records
