"""OAuth2 client-credentials authentication for the EUIPO trademark search API."""

from __future__ import annotations

import time

import httpx

from .errors import EUIPOAuthError

# Refresh slightly before the token actually expires to avoid races near the boundary.
_EXPIRY_SAFETY_MARGIN_SECONDS = 60


class OAuth2ClientCredentials:
    """Fetches and caches an OAuth2 access token using the client-credentials flow.

    The EUIPO API authenticates applications anonymously: we POST the client id
    and secret to the token endpoint and receive a bearer token, which is cached
    until shortly before it expires.
    """

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        token_url: str,
        http_client: httpx.Client,
        scope: str = "uid",
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_url = token_url
        self._http = http_client
        self._scope = scope
        self._token: str | None = None
        self._expires_at: float = 0.0

    def get_token(self, *, force_refresh: bool = False) -> str:
        """Return a valid bearer token, fetching a new one when needed."""
        if not force_refresh and self._token is not None and time.monotonic() < self._expires_at:
            return self._token
        return self._fetch_token()

    def _fetch_token(self) -> str:
        try:
            response = self._http.post(
                self._token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "scope": self._scope,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as exc:
            raise EUIPOAuthError(f"Token request to {self._token_url} failed: {exc}") from exc

        if response.status_code != httpx.codes.OK:
            raise EUIPOAuthError(
                f"Token request failed with status {response.status_code}: {response.text!r}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise EUIPOAuthError(f"Token response was not valid JSON: {response.text!r}") from exc

        token = payload.get("access_token")
        if not token:
            raise EUIPOAuthError(f"Token response did not contain an access_token: {payload!r}")

        expires_in = payload.get("expires_in", 0)
        try:
            expires_in = int(expires_in)
        except (TypeError, ValueError):
            expires_in = 0
        self._token = token
        self._expires_at = time.monotonic() + max(expires_in - _EXPIRY_SAFETY_MARGIN_SECONDS, 0)
        return token
