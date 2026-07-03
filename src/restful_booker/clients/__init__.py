"""HTTP clients, one per restful-booker API resource."""

from restful_booker.clients.auth import AuthClient
from restful_booker.clients.base import BaseClient
from restful_booker.clients.booking import BookingClient
from restful_booker.clients.health import HealthClient

__all__ = ["AuthClient", "BaseClient", "BookingClient", "HealthClient"]
