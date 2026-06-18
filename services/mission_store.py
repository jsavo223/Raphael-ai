from typing import List, Optional

from schemas.mission import Mission
from services.redaction import redact_data
from services.safe_json import SafeJsonStore


class MissionStore:
    def __init__(self, path: str = "data/missions.json"):
        self.json_store = SafeJsonStore(path, default_value=[])
        self.missions: List[Mission] = self._load()

    def _load(self) -> List[Mission]:
        raw_missions = self.json_store.load()
        return [Mission(**mission) for mission in raw_missions]

    def _save(self):
        self.json_store.save(
            [redact_data(mission.model_dump(mode="json")) for mission in self.missions]
        )

    def add(self, mission: Mission):
        redacted_mission = Mission(**redact_data(mission.model_dump(mode="json")))
        self.missions.append(redacted_mission)
        self._save()

    def update(self, mission: Mission):
        redacted_mission = Mission(**redact_data(mission.model_dump(mode="json")))

        for index, existing in enumerate(self.missions):
            if existing.mission_id == redacted_mission.mission_id:
                self.missions[index] = redacted_mission
                self._save()
                return

        self.add(redacted_mission)

    def get_all(self):
        return self.missions

    def get(self, mission_id: str) -> Optional[Mission]:
        for mission in self.missions:
            if mission.mission_id == mission_id:
                return mission
        return None
