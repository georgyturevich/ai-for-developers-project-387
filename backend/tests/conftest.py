"""Shared test scaffolding: a fixed clock and an httpx client over the ASGI app."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import httpx

from cal_bookings.app import create_app

NOW = datetime(2026, 8, 12, 6, 0, 0, tzinfo=UTC)


class MutableClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


@asynccontextmanager
async def api_client(now: datetime = NOW) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(clock=lambda: now)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@asynccontextmanager
async def api_client_with_clock(clock: MutableClock) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(clock=clock)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


EVENT_TYPE = {
    "id": "strizhka",
    "name": "Стрижка",
    "description": "Стрижка и укладка за один час.",
    "durationInMinutes": 60,
}
