# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Minimal Python client for the EUIPO (European Union Intellectual Property Office) trademark search API.

## Architecture

The `euipo_tm_client/` package is a thin, synchronous wrapper over the API (built on `httpx`). Responses are returned as raw parsed JSON (`dict`) — the 70+ spec schemas are intentionally not modeled as classes.

- `config.py` — `Settings` (credentials + environment) loaded via `Settings.from_env()`, plus the per-environment `API_BASE_URLS` / `TOKEN_URLS` maps and a dependency-free `.env` loader (`_load_dotenv`). Real environment variables take precedence over `.env`.
- `auth.py` — `OAuth2ClientCredentials`: fetches and caches the bearer token (client-credentials flow), refreshing ~60s before expiry.
- `client.py` — `TrademarkSearchClient` with `search_trademarks()` (GET `/trademarks`) and `get_trademark()` (GET `/trademarks/{applicationNumber}`). `_get()` injects the two required auth headers and retries once on a 401 (forcing a token refresh). Use as a context manager to close the HTTP pool.
- `errors.py` — `EUIPOError` base; `EUIPOAuthError` (token failures); `EUIPOAPIError(status_code, body)` (non-2xx API responses).

### Authentication (both endpoints)

OAuth2 **client-credentials** flow: POST `grant_type=client_credentials` + `client_id`/`client_secret`/`scope=uid` to the environment's token URL. Every API request must send **both** `Authorization: Bearer <token>` **and** `X-IBM-Client-Id: <client_id>`. The production token URL is the unverified sandbox mirror (`auth.euipo.europa.eu`); confirm/override if EUIPO documents a different one.

## Tooling

This project is managed with [`uv`](https://docs.astral.sh/uv/). Dev uses Python 3.13 (pinned in `.python-version`); the published package targets `>=3.10`. The floor is coupled to dev deps — pytest 9 requires `>=3.10`, so don't lower `requires-python` below that without downgrading pytest.

- Run the app: `uv run main.py`
- Add a dependency: `uv add <package>` (updates `pyproject.toml` + `uv.lock`)
- Sync the environment: `uv sync`
- Run an arbitrary command in the project venv: `uv run <cmd>`
- Build distributions: `uv build`, then validate with `uvx --from twine twine check dist/*`

- Run tests: `uv run pytest` (single test: `uv run pytest tests/test_client.py::test_name`)

Tests live in `tests/` and mock the HTTP layer with `httpx.MockTransport`, so they need no live credentials or API plan subscription.

## Configuration

The client reads credentials from environment variables (loaded from `.env`, which is gitignored):

- `EUIPO_API_KEY`
- `EUIPO_API_SECRET`
- `EUIPO_ENVIRONMENT` — either `"sandbox"` or `"production"`

The `sandbox`/`production` split selects the API base URL; honor `EUIPO_ENVIRONMENT` when wiring up requests rather than hardcoding an endpoint:

- `sandbox` → `https://api-sandbox.euipo.europa.eu/trademark-search`
- `production` → `https://api.euipo.europa.eu/trademark-search`

## API reference

- OpenAPI specification: `specs/openapi.json` — the source of truth for endpoints, request/response schemas, and parameters.
- Authentication details: https://dev-sandbox.euipo.europa.eu/security

### Gotchas

- A `403` "Not registered to plan" means auth succeeded but the app isn't subscribed to the Trademark search plan in the dev portal (account fix, not a code bug).
- `W`-prefixed application numbers (e.g. `W00893924`) are international registrations: `applicationDate` is null — fall back to `designationDate`.
- RSQL `query` param: use `field==*term*` for a contains/wildcard match (see README "Query language (RSQL)").
