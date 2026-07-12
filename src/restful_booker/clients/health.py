"""Client for the /ping health-check resource."""

from __future__ import annotations

import requests

from restful_booker.clients.base import BaseClient


class HealthClient(BaseClient):
    def ping(self) -> requests.Response:
        return self.request("GET", "/ping")
