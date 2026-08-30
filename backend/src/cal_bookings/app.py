"""FastAPI application: thin adapters between the contract and the domain core."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from cal_bookings import domain
from cal_bookings.schemas import (
    Booking,
    CreateBookingRequest,
    EventType,
    EventTypeSummary,
    GuestInfo,
    Slot,
    Slug,
)
from cal_bookings.static import SPAStaticFiles
from cal_bookings.store import DuplicateSlugError, InMemoryStore, SlotUnavailableError

CORS_ALLOWED_ORIGIN = "http://localhost:5173"

MAX_REQUEST_BODY_BYTES = 64 * 1024


class RequestBodyTooLarge(Exception):
    pass


class RequestBodySizeLimitMiddleware:
    """Caps the request body; answers with the contract's 400 validation_failed shape."""

    def __init__(self, app: ASGIApp, max_size: int = MAX_REQUEST_BODY_BYTES) -> None:
        self.app = app
        self.max_size = max_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_size:
                    raise RequestBodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except RequestBodyTooLarge:
            response = JSONResponse(
                status_code=400,
                content={
                    "code": "validation_failed",
                    "message": "Тело запроса превышает лимит в 64 КиБ.",
                },
            )
            await response(scope, receive, send)


def http_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def get_store(request: Request) -> InMemoryStore:
    return request.app.state.store


def get_now(request: Request) -> datetime:
    return request.app.state.clock()


def _booking_response(booking: domain.Booking, event_type: domain.EventType) -> Booking:
    guest_kwargs: dict[str, str] = {"name": booking.guest_name, "email": booking.guest_email}
    if booking.guest_comment is not None:
        guest_kwargs["comment"] = booking.guest_comment
    return Booking(
        id=booking.id,
        event_type=EventTypeSummary(
            id=event_type.id,
            name=event_type.name,
            duration_in_minutes=event_type.duration_in_minutes,
        ),
        start=booking.start,
        guest=GuestInfo(**guest_kwargs),
    )


def create_app(clock: Callable[[], datetime] | None = None) -> FastAPI:
    app = FastAPI(title="Calendar Bookings API")
    app.state.store = InMemoryStore()
    app.state.clock = clock or (lambda: datetime.now(UTC))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[CORS_ALLOWED_ORIGIN],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestBodySizeLimitMiddleware)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error.get('loc', []))}: {error.get('msg', '')}"
            for error in exc.errors()
        )
        return JSONResponse(status_code=400, content={"code": "validation_failed", "message": details})

    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            return JSONResponse(status_code=exc.status_code, content=detail, headers=exc.headers)
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": "validation_failed", "message": str(detail)},
            headers=exc.headers,
        )

    @app.get("/event-types", response_model=list[EventType], tags=["Guest"])
    async def list_event_types(store: Annotated[InMemoryStore, Depends(get_store)]) -> list[EventType]:
        return [
            EventType(
                id=event_type.id,
                name=event_type.name,
                description=event_type.description,
                duration_in_minutes=event_type.duration_in_minutes,
            )
            for event_type in store.list_event_types()
        ]

    @app.post("/event-types", response_model=EventType, status_code=201, tags=["Owner"])
    async def create_event_type(body: EventType, store: Annotated[InMemoryStore, Depends(get_store)]) -> EventType:
        try:
            store.create_event_type(
                domain.EventType(
                    id=body.id,
                    name=body.name,
                    description=body.description,
                    duration_in_minutes=body.duration_in_minutes,
                )
            )
        except DuplicateSlugError:
            raise http_error(409, "duplicate_slug", f"Тип события с id «{body.id}» уже существует.")
        return body

    @app.get("/event-types/{event_type_id}/slots", response_model=list[Slot], tags=["Guest"])
    async def list_slots(
        event_type_id: Slug,
        now: Annotated[datetime, Depends(get_now)],
        store: Annotated[InMemoryStore, Depends(get_store)],
    ) -> list[Slot]:
        event_type = store.get_event_type(event_type_id)
        if event_type is None:
            raise http_error(404, "event_type_not_found", f"Тип события «{event_type_id}» не найден.")
        starts = domain.generate_slot_starts(event_type, now, store.occupied_intervals())
        return [Slot(start=start) for start in starts]

    @app.post(
        "/bookings",
        response_model=Booking,
        status_code=201,
        response_model_exclude_none=True,
        tags=["Guest"],
    )
    async def create_booking(
        body: CreateBookingRequest,
        now: Annotated[datetime, Depends(get_now)],
        store: Annotated[InMemoryStore, Depends(get_store)],
    ) -> Booking:
        event_type = store.get_event_type(body.event_type_id)
        if event_type is None:
            raise http_error(404, "event_type_not_found", f"Тип события «{body.event_type_id}» не найден.")
        if not domain.is_valid_grid_start(body.start, event_type.duration_in_minutes):
            raise http_error(400, "validation_failed", "Старт не лежит на сетке слотов или не помещается в рабочие часы.")
        if domain.is_past(body.start, now):
            raise http_error(400, "validation_failed", "Старт уже в прошлом.")
        if not domain.is_within_window(body.start, now):
            raise http_error(400, "validation_failed", "Старт вне окна записи.")
        try:
            booking = store.create_booking(
                event_type.id,
                body.start,
                event_type.duration_in_minutes,
                body.guest.name,
                body.guest.email,
                body.guest.comment,
            )
        except SlotUnavailableError:
            raise http_error(409, "slot_unavailable", "Слот занят: время пересекается с существующей записью.")
        return _booking_response(booking, event_type)

    @app.get("/bookings", response_model=list[Booking], response_model_exclude_none=True, tags=["Owner"])
    async def list_upcoming_bookings(
        now: Annotated[datetime, Depends(get_now)],
        store: Annotated[InMemoryStore, Depends(get_store)],
    ) -> list[Booking]:
        upcoming = [
            booking
            for booking in store.list_bookings()
            if domain.is_upcoming(
                booking.start + timedelta(minutes=booking.duration_in_minutes),
                now,
            )
        ]
        upcoming.sort(key=lambda booking: booking.start)
        return [_booking_response(booking, store.get_event_type(booking.event_type_id)) for booking in upcoming]

    static_dir = os.environ.get("STATIC_DIR")
    if static_dir:
        app.mount("/", SPAStaticFiles(directory=static_dir, html=True), name="spa")

    return app
