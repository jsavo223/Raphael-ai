import json
from pathlib import Path
from typing import List

from schemas.event import Event
from services.redaction import redact_data


class EventStore:
    def __init__(self, path: str = "data/events.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.events: List[Event] = self._load()

    def _load(self) -> List[Event]:
        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as file:
            raw_events = json.load(file)

        return [Event(**event) for event in raw_events]

    def _save(self):
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                [redact_data(event.model_dump(mode="json")) for event in self.events],
                file,
                indent=2,
            )

    def append(self, event: Event):
        redacted_event = Event(**redact_data(event.model_dump(mode="json")))
        self.events.append(redacted_event)
        self._save()

    def get_all(self):
        return self.events

    def get_by_mission(self, mission_id: str):
        return [event for event in self.events if event.mission_id == mission_id]
