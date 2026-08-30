"""API request/response models mirroring the main.tsp contract exactly."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, alias_generators, field_validator

Slug = Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=100)]
# Strict: bools and non-integral numbers are rejected, never coerced (contract int32).
Duration = Annotated[int, Field(strict=True, ge=1, le=540)]


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class EventType(ApiModel):
    id: Slug
    name: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(max_length=2000)]
    duration_in_minutes: Duration


class EventTypeSummary(ApiModel):
    id: Slug
    name: Annotated[str, Field(max_length=200)]
    duration_in_minutes: Duration


class Slot(ApiModel):
    start: datetime


class GuestInfo(ApiModel):
    name: Annotated[str, Field(min_length=1, max_length=200)]
    # EmailStr's format check caps the effective length below the documented 320.
    email: Annotated[EmailStr, Field(max_length=320)]
    comment: Annotated[str | None, Field(max_length=2000)] = None

    @field_validator("comment", mode="before")
    @classmethod
    def reject_explicit_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("comment must be a string, not null")
        return value


class CreateBookingRequest(ApiModel):
    event_type_id: Slug
    start: datetime
    guest: GuestInfo

    @field_validator("start")
    @classmethod
    def require_timezone_and_normalize_to_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("start must include a timezone offset (RFC 3339)")
        return value.astimezone(UTC)


class Booking(ApiModel):
    id: int
    event_type: EventTypeSummary
    start: datetime
    guest: GuestInfo


class ApiError(ApiModel):
    code: str
    message: str
