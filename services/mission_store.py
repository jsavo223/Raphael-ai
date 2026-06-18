import json
from pathlib import Path
from typing import List, Optional

from schemas.mission import Mission


class MissionStore:
    def __init__(self, path: str = "data/missions.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.missions: List[Mission] = self._load()

    def _load(self) -> List[Mission]:
        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as file:
            raw_missions = json.load(file)

        return [Mission(**mission) for mission in raw_missions]

    def _save(self):
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                [mission.model_dump(mode="json") for mission in self.missions],
                file,
                indent=2,
            )

    def add(self, mission: Mission):
        self.missions.append(mission)
        self._save()

    def update(self, mission: Mission):
        for index, existing in enumerate(self.missions):
            if existing.mission_id == mission.mission_id:
                self.missions[index] = mission
                self._save()
                return

        self.add(mission)

    def get_all(self):
        return self.missions

    def get(self, mission_id: str) -> Optional[Mission]:
        for mission in self.missions:
            if mission.mission_id == mission_id:
                return mission
        return None
