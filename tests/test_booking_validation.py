"""Invalid payloads and unauthorized writes against the /booking resource."""

from __future__ import annotations

import pytest

from restful_booker.clients import BookingClient
from tests.conftest import CreatedBooking, load_test_data

pytestmark = pytest.mark.negative

INVALID_BOOKING_PAYLOADS = [
    pytest.param("invalid/booking_firstname_wrong_type.json", id="firstname-not-a-string"),
    pytest.param("invalid/booking_dates_wrong_type.json", id="bookingdates-not-an-object"),
    pytest.param("invalid/booking_missing_checkout.json", id="missing-checkout-date"),
]


@pytest.mark.parametrize("payload_file", INVALID_BOOKING_PAYLOADS)
def test_invalid_booking_payload_is_rejected(
    booking_client: BookingClient, payload_file: str
) -> None:
    # Quirk: restful-booker reports payload validation failures as 500, not 400.
    response = booking_client.create_booking(load_test_data(payload_file))
    assert response.status_code == 500


def test_update_with_invalid_token_is_forbidden(
    booking_client: BookingClient, booking: CreatedBooking
) -> None:
    response = booking_client.update_booking(
        booking.booking_id, booking.payload, token="not-a-real-token"
    )
    assert response.status_code == 403


def test_delete_with_invalid_token_is_forbidden(
    booking_client: BookingClient, booking: CreatedBooking
) -> None:
    response = booking_client.delete_booking(booking.booking_id, token="not-a-real-token")
    assert response.status_code == 403
