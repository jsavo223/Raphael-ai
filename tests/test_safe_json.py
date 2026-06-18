from services.safe_json import SafeJsonStore


def test_safe_json_store_loads_default_when_missing(tmp_path):
    store = SafeJsonStore(str(tmp_path / "data" / "items.json"), default_value=[])

    assert store.load() == []


def test_safe_json_store_saves_and_loads_value(tmp_path):
    store = SafeJsonStore(str(tmp_path / "data" / "items.json"), default_value=[])

    store.save([{"name": "mission"}])

    assert store.load() == [{"name": "mission"}]


def test_safe_json_store_recovers_corrupt_file(tmp_path):
    path = tmp_path / "data" / "items.json"
    path.parent.mkdir(parents=True)
    path.write_text("not valid json", encoding="utf-8")

    store = SafeJsonStore(str(path), default_value=[])

    assert store.load() == []
    assert path.exists()
    assert path.with_suffix(".json.corrupt").exists()
