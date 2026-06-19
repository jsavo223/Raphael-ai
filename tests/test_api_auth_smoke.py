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


def _request(client, method, path, payload):
    request_method = getattr(client, method.lower())

    if payload is None:
        return request_method(path)

    return request_method(path, json=payload)


def test_root_health_is_public(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "online"


@pytest.mark.parametrize("method,path,payload", PRIVATE_ROUTE_CASES)
def test_private_routes_require_owner_key(client, method, path, payload):
    response = _request(client, method, path, payload)

    assert response.status_code == 401
    assert "owner API key" in response.json()["detail"]
