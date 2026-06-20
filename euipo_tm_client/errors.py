"""Exception types raised by the EUIPO trademark search client."""

from __future__ import annotations

from typing import Any


class EUIPOError(Exception):
    """Base class for all errors raised by this client."""


class EUIPOAuthError(EUIPOError):
    """Raised when OAuth2 token acquisition fails."""


class EUIPOAPIError(EUIPOError):
    """Raised when the trademark search API returns a non-success status.

    Attributes:
        status_code: The HTTP status code returned by the API.
        body: The parsed JSON body (dict) when available, otherwise the raw text.
    """

    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"EUIPO API request failed with status {status_code}: {body!r}")
