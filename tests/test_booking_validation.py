"""Invalid payloads and unauthorized or impossible writes against /booking."""

from __future__ import annotations

import pytest
import requests

from restful_booker.clients import BookingClient
from restful_booker.models import Booking
from tests.conftest import CreatedBooking, load_test_data

pytestmark = pytest.mark.negative

INVALID_BOOKING_PAYLOADS = [
    pytest.param("invalid/booking_firstname_wrong_type.json", id="firstname-not-a-string"),
    pytest.param("invalid/booking_dates_wrong_type.json", id="bookingdates-not-an-object"),
    pytest.param("invalid/booking_missing_checkout.json", id="missing-checkout-date"),
]

MUTATING_METHODS = ["PUT", "PATCH", "DELETE"]


def _mutate(
    client: BookingClient, method: str, booking: CreatedBooking, token: str | None
) -> requests.Response:
    """Dispatch one mutating call; assertions stay in the tests."""
    if method == "PUT":
        return client.update_booking(booking.booking_id, booking.payload, token)
    if method == "PATCH":
        return client.partial_update_booking(booking.booking_id, {"totalprice": 1}, token)
    return client.delete_booking(booking.booking_id, token)


@pytest.mark.parametrize("payload_file", INVALID_BOOKING_PAYLOADS)
def test_invalid_booking_payload_is_rejected(
    booking_client: BookingClient, payload_file: str
) -> None:
    # Quirk: restful-booker reports payload validation failures as 500, not 400.
    response = booking_client.create_booking(load_test_data(payload_file))
    assert response.status_code == 500, response.text


@pytest.mark.parametrize("method", MUTATING_METHODS)
def test_write_without_token_is_forbidden(
    booking_client: BookingClient, booking: CreatedBooking, method: str
) -> None:
    response = _mutate(booking_client, method, booking, token=None)
    assert response.status_code == 403, response.text


@pytest.mark.parametrize("method", MUTATING_METHODS)
def test_write_with_invalid_token_is_forbidden_and_has_no_effect(
    booking_client: BookingClient, booking: CreatedBooking, method: str
) -> None:
    response = _mutate(booking_client, method, booking, token="not-a-real-token")
    assert response.status_code == 403, response.text

    unchanged = booking_client.get_booking(booking.booking_id)
    assert unchanged.status_code == 200, unchanged.text
    assert Booking.model_validate(unchanged.json()) == Booking.model_validate(booking.payload)


@pytest.mark.parametrize("method", MUTATING_METHODS)
def test_write_to_missing_booking_is_method_not_allowed(
    booking_client: BookingClient, booking: CreatedBooking, auth_token: str, method: str
) -> None:
    deleted = booking_client.delete_booking(booking.booking_id, auth_token)
    assert deleted.status_code == 201, deleted.text

    # Quirk: restful-booker answers writes to a nonexistent id with 405, not 404.
    response = _mutate(booking_client, method, booking, auth_token)
    assert response.status_code == 405, response.text
