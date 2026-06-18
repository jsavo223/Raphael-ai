from typing import List

from schemas.event import Event
from services.redaction import redact_data
from services.safe_json import SafeJsonStore


class EventStore:
    def __init__(self, path: str = "data/events.json"):
        self.json_store = SafeJsonStore(path, default_value=[])
        self.events: List[Event] = self._load()

    def _load(self) -> List[Event]:
        raw_events = self.json_store.load()
        return [Event(**event) for event in raw_events]

    def _save(self):
        self.json_store.save(
            [redact_data(event.model_dump(mode="json")) for event in self.events]
        )

    def append(self, event: Event):
        redacted_event = Event(**redact_data(event.model_dump(mode="json")))
        self.events.append(redacted_event)
        self._save()

    def get_all(self):
        return self.events

    def get_by_mission(self, mission_id: str):
        return [event for event in self.events if event.mission_id == mission_id]
