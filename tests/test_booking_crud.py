"""Create, read, update and delete lifecycle of the /booking resource."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from pydantic import TypeAdapter

from restful_booker.clients import BookingClient
from restful_booker.models import Booking, BookingCreated, BookingId
from tests.conftest import CreatedBooking

_BOOKING_ID_LIST = TypeAdapter(list[BookingId])


def test_booking_ids_listing_matches_contract(booking_client: BookingClient) -> None:
    response = booking_client.get_booking_ids()
    assert response.status_code == 200
    ids = _BOOKING_ID_LIST.validate_python(response.json())
    assert isinstance(ids, list)


@pytest.mark.smoke
def test_create_booking_echoes_payload(
    create_booking: Callable[[dict[str, Any]], Any], booking_payload: dict[str, Any]
) -> None:
    response = create_booking(booking_payload)
    assert response.status_code == 200
    created = BookingCreated.model_validate(response.json())
    assert created.booking == Booking.model_validate(booking_payload)


@pytest.mark.smoke
def test_created_booking_can_be_fetched(
    booking_client: BookingClient, booking: CreatedBooking
) -> None:
    response = booking_client.get_booking(booking.booking_id)
    assert response.status_code == 200
    assert Booking.model_validate(response.json()) == Booking.model_validate(booking.payload)


def test_full_update_replaces_booking(
    booking_client: BookingClient, booking: CreatedBooking, auth_token: str
) -> None:
    replacement = {**booking.payload, "totalprice": 111, "additionalneeds": "Late checkout"}
    response = booking_client.update_booking(booking.booking_id, replacement, auth_token)
    assert response.status_code == 200
    assert Booking.model_validate(response.json()) == Booking.model_validate(replacement)


def test_partial_update_changes_only_given_fields(
    booking_client: BookingClient, booking: CreatedBooking, auth_token: str
) -> None:
    response = booking_client.partial_update_booking(
        booking.booking_id, {"totalprice": 1000}, auth_token
    )
    assert response.status_code == 200
    expected = {**booking.payload, "totalprice": 1000}
    assert Booking.model_validate(response.json()) == Booking.model_validate(expected)


def test_deleted_booking_is_gone(
    booking_client: BookingClient, booking: CreatedBooking, auth_token: str
) -> None:
    # Quirk: restful-booker answers a successful DELETE with 201 Created.
    response = booking_client.delete_booking(booking.booking_id, auth_token)
    assert response.status_code == 201
    assert booking_client.get_booking(booking.booking_id).status_code == 404
