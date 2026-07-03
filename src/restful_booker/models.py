"""Response contracts for the restful-booker API.

Every model forbids unknown fields, so a contract drift on the API side
(new, renamed, or removed fields) fails loudly instead of passing silently.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BookingDates(_StrictModel):
    checkin: date
    checkout: date


class Booking(_StrictModel):
    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: str | None = None


class BookingCreated(_StrictModel):
    """Response body of POST /booking."""

    bookingid: int
    booking: Booking


class BookingId(_StrictModel):
    """Single entry in the GET /booking listing."""

    bookingid: int


class AuthToken(_StrictModel):
    """Response body of a successful POST /auth."""

    token: str
