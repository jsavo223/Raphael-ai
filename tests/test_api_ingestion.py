import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.auth import OWNER_API_KEY_ENV, OWNER_API_KEY_HEADER


REPO_ROOT = Path(__file__).resolve().parents[1]
OWNER_API_KEY = "test-owner-key"
OWNER_HEADERS = {OWNER_API_KEY_HEADER: OWNER_API_KEY}


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


def test_external_ingestion_api_accepts_safe_content(client):
    response = client.post(
        "/ingestion/external",
        headers=OWNER_HEADERS,
        json={
            "content": "This external page contains release notes and setup guidance for Raphael AI.",
            "source_type": "web_page",
            "source_id": "docs-page-1",
        },
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
