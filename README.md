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

## Query language (RSQL)

The `query` argument of `search_trademarks()` accepts an **RSQL** (REST Query
Language) expression — a compact, URL-friendly filter syntax. A clause is
`field` + `operator` + `value`, and clauses combine with `and` / `or` (use
parentheses to group). RSQL avoids unsafe characters, so no URL encoding is
needed.

Comparison operators:

| Operator           | Meaning                                  |
| ------------------ | ---------------------------------------- |
| `==`               | equal to (supports `*` as a wildcard)    |
| `!=`               | not equal to (supports `*` as a wildcard)|
| `<` `<=` `>` `>=`  | range comparison (dates and numbers)     |
| `=in=`             | in a set, e.g. `=in=(WORD,FIGURATIVE)`   |
| `=out=`            | not in a set                             |
| `=all=`            | contains all of a set                    |

Each field supports only a subset of these operators. Date fields
(`applicationDate`, `registrationDate`, `expiryDate`, …) expect `yyyy-MM-dd`
values. Examples:

```text
# Verbal element exactly "apple"
wordMarkSpecification.verbalElement==apple

# Wildcard match + status, with nice-class membership
niceClasses=all=(25,28,40) and wordMarkSpecification.verbalElement==*Dog* and status==REGISTERED

# Date range with grouped OR logic
applicationDate>=2023-05-04 and ((markFeature==FIGURATIVE and niceClasses=all=(25,26)) or (markFeature==WORD and niceClasses=out=(40)))
```

The full grammar, the list of supported fields, and the operators each field
allows are documented in the `query` parameter of the OpenAPI spec
(`specs/openapi.json`).

## Development

This project is managed with [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync          # install dependencies
uv run pytest    # run the test suite (mocks HTTP; no live credentials needed)
uv run main.py   # run the live sandbox demo (requires credentials)
```

## Releasing

Releases publish to PyPI automatically when a GitHub Release is published — see
[RELEASING.md](RELEASING.md).

## License

[MIT](LICENSE)
