from schemas.mission import Mission
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
