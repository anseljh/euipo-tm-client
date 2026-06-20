"""Tests for TrademarkSearchClient using a mocked httpx transport.

These exercise request building, auth-header injection, the 401 retry, token
caching, and error mapping without contacting the live EUIPO API.
"""

from __future__ import annotations

import httpx
import pytest

from euipo_tm_client import EUIPOAPIError, Settings, TrademarkSearchClient

SETTINGS = Settings(api_key="cid", api_secret="secret", environment="sandbox")
API_BASE = SETTINGS.api_base_url
TOKEN_URL = SETTINGS.token_url


def _build_client(handler) -> TrademarkSearchClient:
    """Construct a client whose HTTP traffic is served by ``handler``."""
    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    client = TrademarkSearchClient(settings=SETTINGS)
    client._http = http
    client._auth._http = http
    return client


def _token_response() -> httpx.Response:
    return httpx.Response(200, json={"access_token": "tok-123", "expires_in": 28800})


def test_search_sends_params_and_auth_headers() -> None:
    captured: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == TOKEN_URL:
            return _token_response()
        captured["api"] = request
        return httpx.Response(
            200,
            json={
                "trademarks": [],
                "size": 10,
                "totalElements": 0,
                "totalPages": 0,
                "page": 0,
            },
        )

    with _build_client(handler) as client:
        result = client.search_trademarks(
            query="wordMarkSpecification.verbalElement==apple",
            size=25,
            sort="applicationNumber:desc",
        )

    assert result["totalElements"] == 0
    req = captured["api"]
    assert req.url.path == "/trademark-search/trademarks"
    assert req.url.params["query"] == "wordMarkSpecification.verbalElement==apple"
    assert req.url.params["size"] == "25"
    assert req.url.params["sort"] == "applicationNumber:desc"
    assert req.headers["Authorization"] == "Bearer tok-123"
    assert req.headers["X-IBM-Client-Id"] == "cid"


def test_get_trademark_sets_path_and_language() -> None:
    captured: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == TOKEN_URL:
            return _token_response()
        captured["api"] = request
        return httpx.Response(200, json={"applicationNumber": "018692868", "status": "REGISTERED"})

    with _build_client(handler) as client:
        detail = client.get_trademark("018692868", language="en")

    assert detail["status"] == "REGISTERED"
    req = captured["api"]
    assert req.url.path == "/trademark-search/trademarks/018692868"
    assert req.headers["Accept-Language"] == "en"


def test_401_triggers_token_refresh_and_retry() -> None:
    state = {"token_calls": 0, "api_calls": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == TOKEN_URL:
            state["token_calls"] += 1
            return httpx.Response(200, json={"access_token": f"tok-{state['token_calls']}", "expires_in": 28800})
        state["api_calls"] += 1
        if state["api_calls"] == 1:
            return httpx.Response(401, json={"error": "Unauthorized"})
        return httpx.Response(
            200,
            json={"trademarks": [], "size": 10, "totalElements": 0, "totalPages": 0, "page": 0},
        )

    with _build_client(handler) as client:
        client.search_trademarks()

    assert state["api_calls"] == 2
    assert state["token_calls"] == 2  # initial fetch + forced refresh after 401


def test_token_is_cached_across_calls() -> None:
    state = {"token_calls": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == TOKEN_URL:
            state["token_calls"] += 1
            return _token_response()
        return httpx.Response(
            200,
            json={"trademarks": [], "size": 10, "totalElements": 0, "totalPages": 0, "page": 0},
        )

    with _build_client(handler) as client:
        client.search_trademarks()
        client.search_trademarks()

    assert state["token_calls"] == 1


def test_api_error_is_raised_with_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == TOKEN_URL:
            return _token_response()
        return httpx.Response(404, json={"status": 404, "title": "Not Found"})

    with _build_client(handler) as client:
        with pytest.raises(EUIPOAPIError) as exc_info:
            client.get_trademark("000000000")

    assert exc_info.value.status_code == 404
    assert exc_info.value.body["title"] == "Not Found"
