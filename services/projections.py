class MissionProjection:
    def __init__(self):
        self.missions = {}

    def update(self, mission_id: str, status: str, latest_update: str):
        self.missions[mission_id] = {
            "mission_id": mission_id,
            "status": status,
            "latest_update": latest_update
        }

    def get(self, mission_id: str):
        return self.missions.get(mission_id)