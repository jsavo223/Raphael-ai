from schemas.event import Event
from schemas.mission import Mission
from services.event_store import EventStore
from services.mission_store import MissionStore


def test_mission_store_recovers_from_corrupt_json(tmp_path):
    path = tmp_path / "missions.json"
    path.write_text("not valid json", encoding="utf-8")

    store = MissionStore(str(path))

    assert store.get_all() == []
    assert path.exists()
    assert path.with_suffix(".json.corrupt").exists()


def test_mission_store_still_saves_after_recovery(tmp_path):
    path = tmp_path / "missions.json"
    path.write_text("not valid json", encoding="utf-8")

    store = MissionStore(str(path))
    mission = Mission(
        mission_id="mission_test",
        goal="Build a safe test mission",
        status="running",
        created_at="2026-01-01T00:00:00Z",
    )

    store.add(mission)

    reloaded = MissionStore(str(path))
    assert reloaded.get("mission_test") is not None
    assert reloaded.get("mission_test").goal == "Build a safe test mission"


def test_event_store_recovers_from_corrupt_json(tmp_path):
    path = tmp_path / "events.json"
    path.write_text("not valid json", encoding="utf-8")

    store = EventStore(str(path))

    assert store.get_all() == []
    assert path.exists()
    assert path.with_suffix(".json.corrupt").exists()


def test_event_store_still_saves_after_recovery(tmp_path):
    path = tmp_path / "events.json"
    path.write_text("not valid json", encoding="utf-8")

    store = EventStore(str(path))
    event = Event(
        event_id="event_test",
        event_type="MISSION_CREATED",
        mission_id="mission_test",
        timestamp="2026-01-01T00:00:00Z",
        actor_type="control_core",
        actor_id="control_core_main",
        correlation_id="corr_test",
        payload={"goal": "Build a safe test mission"},
        hash="hash_test",
    )

    store.append(event)

    reloaded = EventStore(str(path))
    events = reloaded.get_by_mission("mission_test")
    assert len(events) == 1
    assert events[0].event_type == "MISSION_CREATED"
