"""Client for the /auth resource."""

from __future__ import annotations

import requests

from restful_booker.clients.base import BaseClient


class AuthClient(BaseClient):
    def create_token(self, username: str, password: str) -> requests.Response:
        return self.request("POST", "/auth", json={"username": username, "password": password})
