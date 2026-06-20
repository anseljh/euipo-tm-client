# euipo-tm-client

Minimal Python client for the [EUIPO](https://euipo.europa.eu/) (European Union
Intellectual Property Office) trademark search API.

It is a thin, synchronous wrapper (built on [`httpx`](https://www.python-httpx.org/))
that handles OAuth2 authentication and returns responses as raw parsed JSON
(`dict`). It covers the two core endpoints: searching for trade marks and
retrieving the details of a single trade mark.

## Installation

```bash
pip install euipo-tm-client
```

## Configuration

The client reads credentials from environment variables (you can keep them in a
`.env` file in the working directory — real environment variables take
precedence):

| Variable            | Description                                   |
| ------------------- | --------------------------------------------- |
| `EUIPO_API_KEY`     | Your application's client ID                  |
| `EUIPO_API_SECRET`  | Your application's client secret              |
| `EUIPO_ENVIRONMENT` | `"sandbox"` (default) or `"production"`       |

Obtain credentials and subscribe your application to the *Trademark search* API
plan via the [EUIPO developer portal](https://dev-sandbox.euipo.europa.eu/).

## Usage

```python
from euipo_tm_client import TrademarkSearchClient

with TrademarkSearchClient() as client:
    # Search using an RSQL query expression.
    results = client.search_trademarks(
        query="wordMarkSpecification.verbalElement==apple",
        size=10,
    )
    print(results["totalElements"])
    for tm in results["trademarks"]:
        print(tm["applicationNumber"], tm.get("status"))

    # Retrieve full details for one trade mark.
    detail = client.get_trademark("018692868", language="en")
    print(detail["status"])
```

Credentials and environment can also be passed explicitly instead of via the
environment:

```python
client = TrademarkSearchClient(
    api_key="...", api_secret="...", environment="production",
)
```

### Errors

API and authentication failures raise typed exceptions, all subclasses of
`EUIPOError`:

- `EUIPOAuthError` — token acquisition failed.
- `EUIPOAPIError` — the API returned a non-2xx response; exposes `.status_code`
  and the parsed `.body`.

## Development

This project is managed with [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync          # install dependencies
uv run pytest    # run the test suite (mocks HTTP; no live credentials needed)
uv run main.py   # run the live sandbox demo (requires credentials)
```

## License

[MIT](LICENSE)
