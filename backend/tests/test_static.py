"""Static SPA serving: the STATIC_DIR-gated fallback (ticket #18).

Behavior is asserted on the existing seam — HTTP against the ASGI app — with a
temp directory standing in for the built frontend. The env var is read inside
create_app, so monkeypatching before entering the client is enough.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from _pytest.monkeypatch import MonkeyPatch
from _pytest.tmpdir import TempPathFactory

from tests.conftest import api_client

INDEX = "<!doctype html><html><body>SPA</body></html>"


@pytest.fixture
async def static_client(
    tmp_path_factory: TempPathFactory, monkeypatch: MonkeyPatch
) -> AsyncIterator:
    static_dir = tmp_path_factory.mktemp("static")
    (static_dir / "index.html").write_text(INDEX, encoding="utf-8")
    monkeypatch.setenv("STATIC_DIR", str(static_dir))
    async with api_client() as client:
        yield client


async def test_root_serves_index_when_static_dir_set(static_client):
    response = await static_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert response.text == INDEX


async def test_deep_ui_links_fall_back_to_index(static_client):
    for path in ["/owner", "/types/some-slug/book", "/confirmation"]:
        response = await static_client.get(path)
        assert response.status_code == 200, path
        assert response.headers["content-type"].startswith("text/html"), path
        assert response.text == INDEX, path


async def test_unknown_api_path_stays_json_error(static_client):
    for path in ["/event-types/nope", "/bookings/nope", "/api/v1/nonexistent"]:
        response = await static_client.get(path)
        assert response.status_code == 404, path
        assert response.headers["content-type"].startswith("application/json"), path
        body = response.json()
        assert "code" in body, path
        assert "message" in body, path


async def test_api_routes_still_win_when_static_dir_set(static_client):
    response = await static_client.get("/event-types")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")


async def test_unknown_api_path_keeps_contract_semantics(static_client):
    response = await static_client.get("/event-types/nope/slots")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["code"] == "event_type_not_found"


async def test_without_static_dir_app_stays_api_only(tmp_path, monkeypatch):
    monkeypatch.delenv("STATIC_DIR", raising=False)
    async with api_client() as client:
        for path in ["/", "/owner"]:
            response = await client.get(path)
            assert response.status_code == 404, path
            assert response.headers["content-type"].startswith("application/json"), path
        response = await client.get("/event-types")
        assert response.status_code == 200
