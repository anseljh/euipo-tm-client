"""Synchronous client for the EUIPO trademark search API."""

from __future__ import annotations

from typing import Any

import httpx

from .auth import OAuth2ClientCredentials
from .config import Environment, Settings
from .errors import EUIPOAPIError

DEFAULT_TIMEOUT = 30.0


class TrademarkSearchClient:
    """Client for the EUIPO "Trademark search" API.

    Wraps OAuth2 client-credentials authentication and exposes the two core
    endpoints: :meth:`search_trademarks` and :meth:`get_trademark`. Responses are
    returned as parsed JSON (``dict``).

    Credentials and environment default to the ``EUIPO_*`` environment variables
    (see :meth:`Settings.from_env`) but may be passed explicitly.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        environment: Environment | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        settings: Settings | None = None,
    ) -> None:
        if settings is None:
            if api_key is not None and api_secret is not None:
                settings = Settings(
                    api_key=api_key,
                    api_secret=api_secret,
                    environment=environment or "sandbox",
                )
            else:
                settings = Settings.from_env()
                if environment is not None:
                    settings = Settings(
                        api_key=api_key or settings.api_key,
                        api_secret=api_secret or settings.api_secret,
                        environment=environment,
                    )

        self._settings = settings
        self._http = httpx.Client(timeout=timeout)
        self._auth = OAuth2ClientCredentials(
            client_id=settings.api_key,
            client_secret=settings.api_secret,
            token_url=settings.token_url,
            http_client=self._http,
        )

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> "TrademarkSearchClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # -- endpoints ---------------------------------------------------------

    def search_trademarks(
        self,
        query: str | None = None,
        *,
        fields: str | None = None,
        page: int = 0,
        size: int = 10,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """Search for trade marks (``GET /trademarks``).

        Args:
            query: RSQL filter expression, e.g.
                ``wordMarkSpecification.verbalElement==apple``.
            fields: Field-selection expression; ``*`` returns all fields.
            page: Zero-based page index (default 0).
            size: Page size, 10..100 (default 10).
            sort: Sort expression ``field:asc`` or ``field:desc``.

        Returns:
            The ``TrademarkSearchResult`` payload as a dict.
        """
        params: dict[str, Any] = {"page": page, "size": size}
        if query is not None:
            params["query"] = query
        if fields is not None:
            params["fields"] = fields
        if sort is not None:
            params["sort"] = sort
        return self._get("/trademarks", params=params)

    def get_trademark(
        self,
        application_number: str,
        *,
        fields: str | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve the details of a trade mark (``GET /trademarks/{applicationNumber}``).

        Args:
            application_number: Public identifier, e.g. ``018692868``.
            fields: Field-selection expression; ``*`` returns all fields.
            language: Value for the ``Accept-Language`` header used to filter
                multilingual fields (e.g. ``en``).

        Returns:
            The ``Trademark`` payload as a dict.
        """
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        headers = {"Accept-Language": language} if language else None
        return self._get(
            f"/trademarks/{application_number}",
            params=params or None,
            headers=headers,
        )

    # -- internals ---------------------------------------------------------

    def _get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """GET an API path with auth headers, retrying once on a 401."""
        url = f"{self._settings.api_base_url}{path}"
        response = self._http.get(
            url,
            params=params,
            headers=self._auth_headers(headers),
        )
        # A 401 may mean the cached token expired server-side; refresh once and retry.
        if response.status_code == httpx.codes.UNAUTHORIZED:
            response = self._http.get(
                url,
                params=params,
                headers=self._auth_headers(headers, force_refresh=True),
            )

        if not response.is_success:
            raise EUIPOAPIError(response.status_code, self._safe_body(response))
        return response.json()

    def _auth_headers(
        self,
        extra: dict[str, str] | None = None,
        *,
        force_refresh: bool = False,
    ) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._auth.get_token(force_refresh=force_refresh)}",
            "X-IBM-Client-Id": self._settings.api_key,
            "Accept": "application/json",
        }
        if extra:
            headers.update(extra)
        return headers

    @staticmethod
    def _safe_body(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text
