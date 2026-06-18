from services.limits import MAX_AUDIT_RECORDS_RESPONSE


def _ingest(client, owner_headers, source_id, source_type="web_page"):
    return client.post(
        "/ingestion/external",
        headers=owner_headers,
        json={
            "content": f"External source {source_id} contains normal documentation content.",
            "source_type": source_type,
            "source_id": source_id,
        },
    )


def _block_ingestion(client, owner_headers, source_id):
    return client.post(
        "/ingestion/external",
        headers=owner_headers,
        json={
            "content": "Normal content from an unsupported source.",
            "source_type": "unsupported_source",
            "source_id": source_id,
        },
    )


def test_tool_audit_api_requires_owner_key(client):
    response = client.get("/audit/tool-activity")

    assert response.status_code == 401
    assert "owner API key" in response.json()["detail"]


def test_tool_audit_api_returns_bounded_newest_first_records(client, owner_headers):
    for source_id in ("docs-page-1", "docs-page-2", "docs-page-3"):
        response = _ingest(client, owner_headers, source_id)
        assert response.status_code == 200

    response = client.get(
        "/audit/tool-activity?limit=2",
        headers=owner_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert [
        record["metadata"]["source_id"] for record in body["records"]
    ] == ["docs-page-3", "docs-page-2"]


def test_tool_audit_api_offsets_records(client, owner_headers):
    for source_id in ("docs-page-1", "docs-page-2", "docs-page-3"):
        response = _ingest(client, owner_headers, source_id)
        assert response.status_code == 200

    response = client.get(
        "/audit/tool-activity?limit=1&offset=1",
        headers=owner_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert body["records"][0]["metadata"]["source_id"] == "docs-page-2"


def test_tool_audit_api_filters_by_tool_name(client, owner_headers):
    response = _ingest(client, owner_headers, "docs-page-1")
    assert response.status_code == 200

    audit_response = client.get(
        "/audit/tool-activity?tool_name=external_ingestion",
        headers=owner_headers,
    )

    assert audit_response.status_code == 200
    body = audit_response.json()
    assert body["tool_name"] == "external_ingestion"
    assert body["total"] == 1
    assert body["records"][0]["tool_name"] == "external_ingestion"


def test_tool_audit_api_filters_by_allowed_status(client, owner_headers):
    allowed_response = _ingest(client, owner_headers, "docs-page-1")
    blocked_response = _block_ingestion(client, owner_headers, "blocked-page-1")

    assert allowed_response.status_code == 200
    assert blocked_response.status_code == 403

    allowed_records = client.get(
        "/audit/tool-activity?allowed=true",
        headers=owner_headers,
    )
    blocked_records = client.get(
        "/audit/tool-activity?allowed=false",
        headers=owner_headers,
    )

    assert allowed_records.status_code == 200
    assert blocked_records.status_code == 200

    allowed_body = allowed_records.json()
    blocked_body = blocked_records.json()

    assert allowed_body["allowed"] is True
    assert allowed_body["total"] == 1
    assert all(record["allowed"] is True for record in allowed_body["records"])

    assert blocked_body["allowed"] is False
    assert blocked_body["total"] == 1
    assert all(record["allowed"] is False for record in blocked_body["records"])


def test_tool_audit_api_combines_filters_before_pagination(client, owner_headers):
    allowed_response = _ingest(client, owner_headers, "docs-page-1")
    blocked_response = _block_ingestion(client, owner_headers, "blocked-page-1")

    assert allowed_response.status_code == 200
    assert blocked_response.status_code == 403

    response = client.get(
        "/audit/tool-activity?tool_name=external_ingestion&allowed=false&limit=1",
        headers=owner_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tool_name"] == "external_ingestion"
    assert body["allowed"] is False
    assert body["total"] == 1
    assert body["records"][0]["allowed"] is False
    assert body["records"][0]["metadata"]["source_id"] == "blocked-page-1"


def test_tool_audit_api_rejects_invalid_pagination(client, owner_headers):
    too_small = client.get(
        "/audit/tool-activity?limit=0",
        headers=owner_headers,
    )
    too_large = client.get(
        f"/audit/tool-activity?limit={MAX_AUDIT_RECORDS_RESPONSE + 1}",
        headers=owner_headers,
    )
    negative_offset = client.get(
        "/audit/tool-activity?offset=-1",
        headers=owner_headers,
    )

    assert too_small.status_code == 422
    assert too_large.status_code == 422
    assert negative_offset.status_code == 422


def test_tool_audit_api_rejects_empty_tool_name_filter(client, owner_headers):
    response = client.get(
        "/audit/tool-activity?tool_name=",
        headers=owner_headers,
    )

    assert response.status_code == 422
