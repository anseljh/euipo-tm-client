"""Demo: search the EUIPO trademark API and fetch a single trade mark.

Run with ``uv run main.py``. Requires EUIPO_API_KEY, EUIPO_API_SECRET, and
(optionally) EUIPO_ENVIRONMENT in the environment or a local ``.env`` file.
"""

from euipo_tm_client import EUIPOError, TrademarkSearchClient


def main() -> None:
    with TrademarkSearchClient() as client:
        # 1. Search for word marks containing "apple".
        results = client.search_trademarks(
            query="wordMarkSpecification.verbalElement==apple",
            size=10,
        )
        print(f"Found {results['totalElements']} trade mark(s); showing page {results['page']}:")
        for tm in results["trademarks"]:
            verbal = (tm.get("wordMarkSpecification") or {}).get("verbalElement", "")
            print(f"  {tm.get('applicationNumber')}  {tm.get('status', ''):12}  {verbal}")

        # 2. Fetch full details for one example application.
        if results["trademarks"]:
            application_number = results["trademarks"][0]["applicationNumber"]
            detail = client.get_trademark(application_number, language="en")
            # International registrations (W... numbers) have no applicationDate;
            # fall back to the EU designation date.
            filing_date = detail.get("applicationDate") or detail.get("designationDate")
            print(f"\nDetails for {application_number}:")
            print(f"  status:           {detail.get('status')}")
            print(f"  filing date:      {filing_date}")
            print(f"  mark feature:     {detail.get('markFeature')}")


if __name__ == "__main__":
    try:
        main()
    except EUIPOError as exc:
        raise SystemExit(f"EUIPO request failed: {exc}")
