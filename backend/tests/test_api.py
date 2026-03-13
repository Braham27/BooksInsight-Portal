import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_create_case_requires_auth(client):
    resp = await client.post("/api/cases", json={})
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_cases_requires_auth(client):
    resp = await client.get("/api/cases")
    assert resp.status_code in (401, 403)
