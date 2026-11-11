"""Mid-market exchange rates (ECB reference rates via the Frankfurter API), cached in a CSV.

Rates are local currency per US dollar. The cache means tests and the index
never depend on a live API call.
"""
import os
from datetime import date as _date

import pandas as pd
import requests

API_URL = "https://api.frankfurter.dev/v1/{date}"
CURRENCIES = ["MXN", "INR", "PHP"]
CACHE_COLUMNS = ["requested_date", "rate_date", "currency", "usd_to_local"]
DEFAULT_CACHE = "data/rates_cache.csv"


def fetch_rates(date):
    """Ask Frankfurter for one day. On weekends and holidays the API returns the
    most recent business day, and 'rate_date' records which day it really was."""
    r = requests.get(
        API_URL.format(date=date),
        params={"base": "EUR", "symbols": "USD," + ",".join(CURRENCIES)},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    rates = data["rates"]
    return [
        {
            "requested_date": date,
            "rate_date": data["date"],
            "currency": cur,
            "usd_to_local": round(rates[cur] / rates["USD"], 4),  # EUR/local divided by EUR/USD
        }
        for cur in CURRENCIES
    ]


def _read_cache(path):
    if os.path.exists(path):
        return pd.read_csv(path, dtype={"requested_date": str, "rate_date": str, "currency": str})
    return pd.DataFrame(columns=CACHE_COLUMNS)


def get_mid_rate(currency, date, cache_path=DEFAULT_CACHE, fetcher=fetch_rates):
    """Mid-market rate (local currency per USD) for a currency on a date like '2026-03-14'.
    Reads the cache first. If the date is missing, fetches it and saves it."""
    if currency not in CURRENCIES:
        raise ValueError(f"Unsupported currency: {currency!r}. Use one of {CURRENCIES}.")
    date = str(date)
    try:
        _date.fromisoformat(date)
    except ValueError:
        raise ValueError(f"Date must look like 2026-03-14, got {date!r}.")

    cache = _read_cache(cache_path)
    hit = cache[(cache["requested_date"] == date) & (cache["currency"] == currency)]
    if not hit.empty:
        return float(hit.iloc[0]["usd_to_local"])

    new_rows = fetcher(date)
    cache = pd.concat([cache, pd.DataFrame(new_rows)], ignore_index=True)
    cache = cache.drop_duplicates(["requested_date", "currency"])
    os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
    cache.to_csv(cache_path, index=False)
    return float(next(row["usd_to_local"] for row in new_rows if row["currency"] == currency))
