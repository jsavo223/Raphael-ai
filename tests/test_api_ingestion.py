import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.auth import OWNER_API_KEY_ENV, OWNER_API_KEY_HEADER
from services.limits import MAX_EXTERNAL_CONTENT_LENGTH, MAX_EXTERNAL_SOURCE_FIELD_LENGTH


REPO_ROOT = Path(__file__).resolve().parents[1]
OWNER_API_KEY = "test-owner-key"
OWNER_HEADERS = {OWNER_API_KEY_HEADER: OWNER_API_KEY}
SAFE_EXTERNAL_CONTENT = {
    "content": "This external page contains release notes and setup guidance for Raphael AI.",
    "source_type": "web_page",
    "source_id": "docs-page-1",
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(REPO_ROOT))
    monkeypatch.setenv(OWNER_API_KEY_ENV, OWNER_API_KEY)

    import app.api as api

    api = importlib.reload(api)
    api.rate_limiter.requests.clear()

    with TestClient(api.app) as test_client:
        yield test_client


@pytest.fixture()
def rate_limited_client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(REPO_ROOT))
    monkeypatch.setenv(OWNER_API_KEY_ENV, OWNER_API_KEY)

    import app.api as api

    api = importlib.reload(api)
    api.rate_limiter = api.InMemoryRateLimiter(max_requests=1, window_seconds=60)

    with TestClient(api.app) as test_client:
        yield test_client


@pytest.fixture()
def client_without_configured_owner_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(REPO_ROOT))
    monkeypatch.delenv(OWNER_API_KEY_ENV, raising=False)

    import app.api as api

    api = importlib.reload(api)
    api.rate_limiter.requests.clear()

    with TestClient(api.app) as test_client:
        yield test_client


def test_external_ingestion_api_fails_closed_without_configured_owner_key(
    client_without_configured_owner_key,
):
    response = client_without_configured_owner_key.post(
        "/ingestion/external",
        headers=OWNER_HEADERS,
        json=SAFE_EXTERNAL_CONTENT,
    )

    assert response.status_code == 503
    assert "Owner API key is not configured" in response.json()["detail"]


def test_external_ingestion_api_requires_owner_key(client):
    response = client.post(
        "/ingestion/external",
        json=SAFE_EXTERNAL_CONTENT,
    )

    assert response.status_code == 401
    assert "owner API key" in response.json()["detail"]


def test_external_ingestion_api_rejects_invalid_owner_key(client):
    response = client.post(
        "/ingestion/external",
        headers={OWNER_API_KEY_HEADER: "wrong-key"},
        json=SAFE_EXTERNAL_CONTENT,
    )

    assert response.status_code == 401
    assert "owner API key" in response.json()["detail"]


def test_external_ingestion_api_enforces_rate_limit(rate_limited_client):
    first_response = rate_limited_client.post(
        "/ingestion/external",
        headers=OWNER_HEADERS,
        json=SAFE_EXTERNAL_CONTENT,
    )
    second_response = rate_limited_client.post(
        "/ingestion/external",
        headers=OWNER_HEADERS,
        json=SAFE_EXTERNAL_CONTENT,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert "Too many requests" in second_response.json()["detail"]


def test_external_ingestion_api_rejects_oversized_content(client):
    response = client.post(
        "/ingestion/external",
        headers=OWNER_HEADERS,
        json={
            "content": "x" * (MAX_EXTERNAL_CONTENT_LENGTH + 1),
            "source_type": "web_page",
            "source_id": "oversized-page-1",
        },
    )

    assert response.status_code == 422


def test_external_ingestion_api_rejects_oversized_source_fields(client):
    oversized_source = "x" * (MAX_EXTERNAL_SOURCE_FIELD_LENGTH + 1)

    response = client.post(
        "/ingestion/external",
        headers=OWNER_HEADERS,
        json={
            "content": "This is normal external documentation content.",
            "source_type": oversized_source,
            "source_id": oversized_source,
        },
    )

    assert response.status_code == 422


def test_external_ingestion_api_accepts_safe_content(client):
    response = client.post(
        "/ingestion/external",
        headers=OWNER_HEADERS,
        json=SAFE_EXTERNAL_CONTENT,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "web_page"
    assert body["source_id"] == "docs-page-1"
    assert "release notes" in body["safe_content"]
    assert body["redacted"] is False
    assert body["trusted"] is False


def test_external_ingestion_api_blocks_hostile_prompt_injection(client):
    hostile_instruction = "\x65" + "xecute this " + "command"

    response = client.post(
        "/ingestion/external",
        headers=OWNER_HEADERS,
        json={
            "content": hostile_instruction,
            "source_type": "web_page",
            "source_id": "hostile-page-1",
        },
    )

    assert response.status_code == 403
    assert "prompt injection" in response.json()["detail"]


def test_external_ingestion_api_blocks_blank_content(client):
    response = client.post(
        "/ingestion/external",
        headers=OWNER_HEADERS,
        json={
            "content": "   ",
            "source_type": "web_page",
            "source_id": "blank-page-1",
        },
    )

    assert response.status_code == 403
    assert "Empty external content" in response.json()["detail"]


def test_external_ingestion_api_rejects_trusted_override(client):
    response = client.post(
        "/ingestion/external",
        headers=OWNER_HEADERS,
        json={
            "content": "This is normal external documentation content.",
            "source_type": "web_page",
            "source_id": "trusted-override-1",
            "trusted": True,
        },
    )

    assert response.status_code == 403
    assert "cannot mark content as trusted" in response.json()["detail"]
