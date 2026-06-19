import pytest


PRIVATE_ROUTE_CASES = [
    ("GET", "/health", None),
    ("POST", "/chat", {"message": "hello"}),
    (
        "POST",
        "/ingestion/external",
        {
            "content": "This external page contains normal documentation content.",
            "source_type": "web_page",
            "source_id": "auth-smoke-page-1",
        },
    ),
    ("GET", "/audit/tool-activity", None),
    ("POST", "/missions", {"goal": "Build a simple smoke-test mission."}),
    ("GET", "/missions", None),
    ("GET", "/missions/missing-mission/status", None),
    ("GET", "/missions/missing-mission", None),
    ("GET", "/missions/missing-mission/events", None),
    ("GET", "/training/suggestions", None),
    (
        "POST",
        "/training/suggestions",
        {
            "title": "Smoke test suggestion",
            "description": "Verify private endpoints require owner auth.",
        },
    ),
    ("GET", "/training/suggestions/missing-suggestion", None),
    ("POST", "/training/suggestions/missing-suggestion/approve", {}),
    ("POST", "/training/suggestions/missing-suggestion/reject", {}),
    ("POST", "/training/suggestions/missing-suggestion/mark-tested", {}),
    ("POST", "/training/suggestions/missing-suggestion/apply", {}),
    ("POST", "/training/analyze-mission/missing-mission", None),
]

READ_ONLY_OWNER_ROUTE_CASES = [
    ("GET", "/health", 200),
    ("GET", "/audit/tool-activity", 200),
    ("GET", "/missions", 200),
    ("GET", "/missions/missing-mission/status", 404),
    ("GET", "/missions/missing-mission", 404),
    ("GET", "/missions/missing-mission/events", 404),
    ("GET", "/training/suggestions", 200),
    ("GET", "/training/suggestions/missing-suggestion", 404),
]


def _request(client, method, path, payload=None, headers=None):
    request_method = getattr(client, method.lower())

    if payload is None:
        return request_method(path, headers=headers)

    return request_method(path, json=payload, headers=headers)


def test_root_health_is_public(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "online"


@pytest.mark.parametrize("method,path,payload", PRIVATE_ROUTE_CASES)
def test_private_routes_require_owner_key(client, method, path, payload):
    response = _request(client, method, path, payload)

    assert response.status_code == 401
    assert "owner API key" in response.json()["detail"]


@pytest.mark.parametrize("method,path,expected_status", READ_ONLY_OWNER_ROUTE_CASES)
def test_read_only_private_routes_accept_owner_key(
    client,
    owner_headers,
    method,
    path,
    expected_status,
):
    response = _request(client, method, path, headers=owner_headers)

    assert response.status_code == expected_status


def test_read_only_private_routes_do_not_mutate_state(client, owner_headers):
    for method, path, _expected_status in READ_ONLY_OWNER_ROUTE_CASES:
        _request(client, method, path, headers=owner_headers)

    missions_response = client.get("/missions", headers=owner_headers)
    suggestions_response = client.get("/training/suggestions", headers=owner_headers)
    audit_response = client.get("/audit/tool-activity", headers=owner_headers)

    assert missions_response.status_code == 200
    assert suggestions_response.status_code == 200
    assert audit_response.status_code == 200
    assert missions_response.json()["missions"] == []
    assert suggestions_response.json()["suggestions"] == []
    assert audit_response.json()["total"] == 0
    assert audit_response.json()["records"] == []
