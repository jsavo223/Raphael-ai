from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.control_core import ControlCore


app = FastAPI(
    title="Raphael AI",
    version="0.1.0"
)

control_core = ControlCore()


class MissionRequest(BaseModel):
    goal: str


@app.get("/")
def health():
    return {
        "status": "online",
        "service": "raphael-ai",
        "version": "0.1.0"
    }


@app.get("/health")
def detailed_health():
    return {
        "status": "healthy",
        "mission_store": "connected",
        "event_store": "connected",
        "worker_pool": "connected"
    }


@app.post("/missions")
def create_mission(request: MissionRequest):
    return control_core.create_mission(request.goal)


@app.get("/missions")
def list_missions():
    return {
        "missions": control_core.mission_store.get_all()
    }


@app.get("/missions/{mission_id}")
def get_mission(mission_id: str):
    mission = control_core.mission_store.get(mission_id)

    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    return mission


@app.get("/missions/{mission_id}/events")
def get_mission_events(mission_id: str):
    mission = control_core.mission_store.get(mission_id)

    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    return {
        "mission_id": mission_id,
        "events": control_core.event_store.get_by_mission(mission_id)
    }
