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


def test_booking_ids_listing_matches_contract(
    booking_client: BookingClient, booking: CreatedBooking
) -> None:
    response = booking_client.get_booking_ids()
    assert response.status_code == 200, response.text
    ids = _BOOKING_ID_LIST.validate_python(response.json())
    assert booking.booking_id in [entry.bookingid for entry in ids]


def test_booking_ids_can_be_filtered_by_name(
    booking_client: BookingClient, booking: CreatedBooking
) -> None:
    response = booking_client.get_booking_ids(
        firstname=booking.payload["firstname"], lastname=booking.payload["lastname"]
    )
    assert response.status_code == 200, response.text
    ids = _BOOKING_ID_LIST.validate_python(response.json())
    # Names are not unique on a shared instance, so assert membership by id.
    assert booking.booking_id in [entry.bookingid for entry in ids]


@pytest.mark.smoke
def test_create_booking_echoes_payload(
    create_booking: Callable[[dict[str, Any]], Any], booking_payload: dict[str, Any]
) -> None:
    response = create_booking(booking_payload)
    assert response.status_code == 200, response.text
    created = BookingCreated.model_validate(response.json())
    assert created.booking == Booking.model_validate(booking_payload)


def test_create_booking_without_optional_field(
    create_booking: Callable[[dict[str, Any]], Any], booking_payload: dict[str, Any]
) -> None:
    booking_payload.pop("additionalneeds")
    response = create_booking(booking_payload)
    assert response.status_code == 200, response.text
    created = BookingCreated.model_validate(response.json())
    assert created.booking.additionalneeds is None


@pytest.mark.smoke
def test_created_booking_can_be_fetched(
    booking_client: BookingClient, booking: CreatedBooking
) -> None:
    response = booking_client.get_booking(booking.booking_id)
    assert response.status_code == 200, response.text
    assert Booking.model_validate(response.json()) == Booking.model_validate(booking.payload)


def test_full_update_replaces_booking(
    booking_client: BookingClient, booking: CreatedBooking, auth_token: str
) -> None:
    replacement = {**booking.payload, "totalprice": 111, "additionalneeds": "Late checkout"}
    response = booking_client.update_booking(booking.booking_id, replacement, auth_token)
    assert response.status_code == 200, response.text
    assert Booking.model_validate(response.json()) == Booking.model_validate(replacement)


PARTIAL_UPDATES = [
    pytest.param({"totalprice": 1000}, id="single-scalar"),
    pytest.param({"firstname": "Changed", "lastname": "Entirely"}, id="two-fields"),
    pytest.param(
        {"bookingdates": {"checkin": "2027-03-01", "checkout": "2027-03-05"}},
        id="nested-dates",
    ),
]


@pytest.mark.parametrize("patch", PARTIAL_UPDATES)
def test_partial_update_changes_only_given_fields(
    booking_client: BookingClient,
    booking: CreatedBooking,
    auth_token: str,
    patch: dict[str, Any],
) -> None:
    response = booking_client.partial_update_booking(booking.booking_id, patch, auth_token)
    assert response.status_code == 200, response.text
    expected = {**booking.payload, **patch}
    assert Booking.model_validate(response.json()) == Booking.model_validate(expected)


def test_deleted_booking_is_gone(
    booking_client: BookingClient, booking: CreatedBooking, auth_token: str
) -> None:
    # Quirk: restful-booker answers a successful DELETE with 201 Created.
    response = booking_client.delete_booking(booking.booking_id, auth_token)
    assert response.status_code == 201, response.text
    assert booking_client.get_booking(booking.booking_id).status_code == 404
