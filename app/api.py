from fastapi import FastAPI
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


@app.post("/missions")
def create_mission(request: MissionRequest):
    return control_core.create_mission(request.goal)