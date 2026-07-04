"""Token creation via the /auth endpoint."""

from __future__ import annotations

import pytest

from restful_booker.clients import AuthClient
from restful_booker.models import AuthToken


@pytest.mark.smoke
def test_valid_credentials_yield_a_token(
    auth_client: AuthClient, credentials: tuple[str, str]
) -> None:
    response = auth_client.create_token(*credentials)
    assert response.status_code == 200
    token = AuthToken.model_validate(response.json())
    assert token.token


INVALID_CREDENTIALS = [
    pytest.param("admin", "definitely-not-the-password", id="wrong-password"),
    pytest.param("no-such-user", "password123", id="unknown-user"),
    pytest.param("admin", "", id="empty-password"),
]


@pytest.mark.negative
@pytest.mark.parametrize(("username", "password"), INVALID_CREDENTIALS)
def test_invalid_credentials_are_rejected(
    auth_client: AuthClient, username: str, password: str
) -> None:
    # Quirk: restful-booker rejects bad credentials with 200 + a reason body,
    # not 401 — asserting the body is the only way to detect the failure.
    response = auth_client.create_token(username, password)
    assert response.status_code == 200, response.text
    assert response.json() == {"reason": "Bad credentials"}
