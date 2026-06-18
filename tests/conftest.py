import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.auth import OWNER_API_KEY_ENV, OWNER_API_KEY_HEADER


REPO_ROOT = Path(__file__).resolve().parents[1]
OWNER_API_KEY = "test-owner-key"


def _load_api(tmp_path, monkeypatch, configure_owner_key=True):
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(REPO_ROOT))

    if configure_owner_key:
        monkeypatch.setenv(OWNER_API_KEY_ENV, OWNER_API_KEY)
    else:
        monkeypatch.delenv(OWNER_API_KEY_ENV, raising=False)

    import app.api as api

    api = importlib.reload(api)
    api.rate_limiter.requests.clear()
    return api


@pytest.fixture()
def owner_headers():
    return {OWNER_API_KEY_HEADER: OWNER_API_KEY}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    api = _load_api(tmp_path, monkeypatch)

    with TestClient(api.app) as test_client:
        yield test_client


@pytest.fixture()
def rate_limited_client(tmp_path, monkeypatch):
    api = _load_api(tmp_path, monkeypatch)
    api.rate_limiter = api.InMemoryRateLimiter(max_requests=1, window_seconds=60)

    with TestClient(api.app) as test_client:
        yield test_client


@pytest.fixture()
def client_without_configured_owner_key(tmp_path, monkeypatch):
    api = _load_api(tmp_path, monkeypatch, configure_owner_key=False)

    with TestClient(api.app) as test_client:
        yield test_client
