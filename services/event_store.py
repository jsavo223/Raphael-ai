from typing import List

from schemas.event import Event


class EventStore:
    def __init__(self):
        self.events: List[Event] = []

    def append(self, event: Event):
        self.events.append(event)

    def get_all(self):
        return self.events