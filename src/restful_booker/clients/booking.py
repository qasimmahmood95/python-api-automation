"""Client for the /booking resource."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import requests

from restful_booker.clients.base import BaseClient


def _token_cookie(token: str) -> dict[str, str]:
    # restful-booker authorizes write operations via a token cookie.
    return {"Cookie": f"token={token}"}


class BookingClient(BaseClient):
    def get_booking_ids(self, **filters: str) -> requests.Response:
        """List booking ids, optionally filtered (firstname, lastname, checkin, checkout)."""
        return self.request("GET", "/booking", params=filters or None)

    def get_booking(self, booking_id: int) -> requests.Response:
        return self.request("GET", f"/booking/{booking_id}")

    def create_booking(self, payload: Mapping[str, Any]) -> requests.Response:
        return self.request("POST", "/booking", json=payload)

    def update_booking(
        self, booking_id: int, payload: Mapping[str, Any], token: str
    ) -> requests.Response:
        return self.request(
            "PUT", f"/booking/{booking_id}", json=payload, headers=_token_cookie(token)
        )

    def partial_update_booking(
        self, booking_id: int, payload: Mapping[str, Any], token: str
    ) -> requests.Response:
        return self.request(
            "PATCH", f"/booking/{booking_id}", json=payload, headers=_token_cookie(token)
        )

    def delete_booking(self, booking_id: int, token: str) -> requests.Response:
        return self.request("DELETE", f"/booking/{booking_id}", headers=_token_cookie(token))
