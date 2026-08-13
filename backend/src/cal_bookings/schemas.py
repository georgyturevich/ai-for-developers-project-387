"""API request/response models mirroring the main.tsp contract exactly."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, alias_generators, field_validator

Slug = Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
Duration = Annotated[int, Field(ge=1, le=540)]


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class EventType(ApiModel):
    id: Slug
    name: Annotated[str, Field(min_length=1)]
    description: str
    duration_in_minutes: Duration


class EventTypeSummary(ApiModel):
    id: Slug
    name: str
    duration_in_minutes: Duration


class Slot(ApiModel):
    start: datetime


class GuestInfo(ApiModel):
    name: Annotated[str, Field(min_length=1)]
    email: EmailStr
    comment: str | None = None

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


class Booking(ApiModel):
    id: int
    event_type: EventTypeSummary
    start: datetime
    guest: GuestInfo


class ApiError(ApiModel):
    code: str
    message: str
