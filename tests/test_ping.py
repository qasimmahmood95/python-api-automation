"""Health check for the /ping endpoint."""

from __future__ import annotations

import pytest

from restful_booker.clients import HealthClient

pytestmark = pytest.mark.smoke


def test_ping_answers_created(health_client: HealthClient) -> None:
    # Quirk: restful-booker's health check deliberately answers 201 Created,
    # not 200 — asserting 201 here is intentional.
    response = health_client.ping()
    assert response.status_code == 201
