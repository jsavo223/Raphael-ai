def test_owner_can_create_and_read_mission(client, owner_headers):
    create_response = client.post(
        "/missions",
        headers=owner_headers,
        json={"goal": "Run a safe write-route smoke test mission."},
    )

    assert create_response.status_code == 200
    created = create_response.json()
    mission_id = created["mission_id"]
    assert created["goal"] == "Run a safe write-route smoke test mission."
    assert created["status"] in ("completed", "failed")
    assert len(created["plan"]) == 3

    list_response = client.get("/missions", headers=owner_headers)
    read_response = client.get(f"/missions/{mission_id}", headers=owner_headers)
    status_response = client.get(f"/missions/{mission_id}/status", headers=owner_headers)
    events_response = client.get(f"/missions/{mission_id}/events", headers=owner_headers)

    assert list_response.status_code == 200
    assert read_response.status_code == 200
    assert status_response.status_code == 200
    assert events_response.status_code == 200

    missions = list_response.json()["missions"]
    assert len(missions) == 1
    assert missions[0]["mission_id"] == mission_id
    assert read_response.json()["mission_id"] == mission_id

    status = status_response.json()
    assert status["mission_id"] == mission_id
    assert status["task_count"] == 3
    assert status["progress_percentage"] >= 0

    events = events_response.json()["events"]
    event_types = [event["event_type"] for event in events]
    assert "MISSION_CREATED" in event_types
    assert "MISSION_PLANNED" in event_types
    assert event_types[-1] in ("MISSION_COMPLETED", "MISSION_FAILED")


def test_owner_can_create_and_read_training_suggestion(client, owner_headers):
    create_response = client.post(
        "/training/suggestions",
        headers=owner_headers,
        json={
            "title": "Write-route smoke suggestion",
            "description": "Verify owner-authenticated training suggestion creation.",
            "target_agent": "training_agent",
            "category": "test_coverage",
            "priority": "low",
            "evidence": ["created_by=api_write_smoke_test"],
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    suggestion_id = created["suggestion_id"]
    assert created["title"] == "Write-route smoke suggestion"
    assert created["status"] == "proposed"
    assert created["target_agent"] == "training_agent"

    list_response = client.get("/training/suggestions", headers=owner_headers)
    read_response = client.get(
        f"/training/suggestions/{suggestion_id}",
        headers=owner_headers,
    )

    assert list_response.status_code == 200
    assert read_response.status_code == 200

    suggestions = list_response.json()["suggestions"]
    assert len(suggestions) == 1
    assert suggestions[0]["suggestion_id"] == suggestion_id
    assert read_response.json()["suggestion_id"] == suggestion_id
