"""Shared fixtures for the restful-booker test suite."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from faker import Faker

from restful_booker.clients import AuthClient, BookingClient, HealthClient

logger = logging.getLogger("restful_booker.tests")

DATA_DIR = Path(__file__).parent / "data"

# restful-booker tolerates DELETE on an already-removed booking with 405,
# so both count as "cleaned up" during teardown.
_DELETED_OK = (201, 404, 405)


@dataclass(frozen=True)
class CreatedBooking:
    booking_id: int
    payload: dict[str, Any]


def load_test_data(relative_path: str) -> Any:
    """Load a JSON payload from tests/data, independent of the CWD."""
    with (DATA_DIR / relative_path).open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="session")
def base_url(request: pytest.FixtureRequest) -> str:
    """Target base URL: the --base-url flag, else the pyproject.toml default.

    Overrides pytest-base-url's fixture because that plugin resolves the ini
    fallback only on the xdist controller, so a bare `pytest -n auto` would
    hand every worker base_url=None and crash the whole suite.
    """
    url = request.config.getoption("base_url") or request.config.getini("base_url")
    if not url:
        pytest.fail("no base URL configured: pass --base-url or set base_url in pyproject.toml")
    return str(url)


@pytest.fixture(scope="session")
def credentials() -> tuple[str, str]:
    """Auth credentials; the defaults are restful-booker's published demo creds."""
    return (
        os.environ.get("BOOKER_USERNAME", "admin"),
        os.environ.get("BOOKER_PASSWORD", "password123"),
    )


@pytest.fixture(scope="session")
def health_client(base_url: str) -> HealthClient:
    return HealthClient(base_url)


@pytest.fixture(scope="session")
def auth_client(base_url: str) -> AuthClient:
    return AuthClient(base_url)


@pytest.fixture(scope="session")
def booking_client(base_url: str) -> BookingClient:
    return BookingClient(base_url)


@pytest.fixture(scope="session")
def auth_token(auth_client: AuthClient, credentials: tuple[str, str]) -> str:
    """A valid auth token, created once per session (i.e. once per xdist worker)."""
    response = auth_client.create_token(*credentials)
    assert response.status_code == 200, f"token request failed: {response.text}"
    body = response.json()
    # Bad credentials also answer 200, but with {"reason": ...} instead of a token.
    assert "token" in body, f"no token issued: {body}"
    return str(body["token"])


fake = Faker()


@pytest.fixture
def booking_payload() -> dict[str, Any]:
    """A unique valid booking payload per test, logged so failures are reproducible."""
    checkin = fake.date_between(start_date="+1d", end_date="+60d")
    checkout = checkin + timedelta(days=fake.random_int(min=1, max=14))
    payload = {
        "firstname": fake.first_name(),
        "lastname": fake.last_name(),
        "totalprice": fake.random_int(min=50, max=5000),
        "depositpaid": fake.boolean(),
        "bookingdates": {"checkin": checkin.isoformat(), "checkout": checkout.isoformat()},
        "additionalneeds": fake.random_element(("Breakfast", "Late checkout", "Extra pillows")),
    }
    logger.info("generated booking payload: %s", payload)
    return payload


@pytest.fixture
def create_booking(
    booking_client: BookingClient, auth_token: str
) -> Iterator[Callable[[dict[str, Any]], Any]]:
    """Factory that POSTs a booking and guarantees deletion during teardown.

    Assertions stay in the tests; the factory only tracks ids it can see so
    that every booking a test creates is removed from the shared system.
    """
    created_ids: list[int] = []

    def _create(payload: dict[str, Any]) -> Any:
        response = booking_client.create_booking(payload)
        if response.status_code == 200:
            body = response.json()
            if isinstance(body, dict) and "bookingid" in body:
                created_ids.append(body["bookingid"])
        return response

    yield _create

    for booking_id in created_ids:
        cleanup = booking_client.delete_booking(booking_id, auth_token)
        if cleanup.status_code not in _DELETED_OK:
            logger.warning("cleanup of booking %s answered %s", booking_id, cleanup.status_code)


@pytest.fixture
def booking(
    create_booking: Callable[[dict[str, Any]], Any], booking_payload: dict[str, Any]
) -> CreatedBooking:
    """A booking that exists for the duration of the test, then gets deleted."""
    response = create_booking(booking_payload)
    assert response.status_code == 200, f"fixture booking failed: {response.text}"
    return CreatedBooking(booking_id=response.json()["bookingid"], payload=booking_payload)
