"""Shared HTTP plumbing for all API clients."""

from __future__ import annotations

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("restful_booker")

DEFAULT_TIMEOUT_SECONDS = 10.0


def _log_response(response: requests.Response, **_: Any) -> None:
    logger.info(
        "%s %s -> %s in %.0f ms",
        response.request.method,
        response.request.url,
        response.status_code,
        response.elapsed.total_seconds() * 1000,
    )


class BaseClient:
    """A `requests.Session` wrapper with base-URL joining, timeouts, retries and logging.

    Retries cover connection failures only — never HTTP status codes — so tests
    asserting on 4xx/5xx see the first real response, and non-idempotent POSTs
    are never replayed after the request body has been sent.
    """

    def __init__(self, base_url: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        if not base_url:
            raise ValueError(
                "base_url is required - pass --base-url or set the base_url ini option"
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        # Connection-setup failures only: no status-based retries (tests assert
        # on 4xx/5xx), no read retries (a request whose body was already sent
        # must never be silently replayed), no Retry-After sleeps.
        retry = Retry(
            total=None,
            connect=3,
            read=0,
            redirect=0,
            status=0,
            other=0,
            backoff_factor=0.5,
            respect_retry_after_header=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.hooks["response"].append(_log_response)

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(method, f"{self.base_url}{path}", **kwargs)
