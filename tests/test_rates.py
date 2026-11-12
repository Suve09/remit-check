import pandas as pd
import pytest
from remitcheck.rates import get_mid_rate


class FakeFetcher:
    """Stands in for the real API so tests never touch the internet."""
    def __init__(self, rate_date_for=None):
        self.calls = []
        self.rate_date_for = rate_date_for or {}

    def __call__(self, date):
        self.calls.append(date)
        rate_date = self.rate_date_for.get(date, date)
        return [
            {"requested_date": date, "rate_date": rate_date, "currency": "MXN", "usd_to_local": 17.85},
            {"requested_date": date, "rate_date": rate_date, "currency": "INR", "usd_to_local": 86.50},
            {"requested_date": date, "rate_date": rate_date, "currency": "PHP", "usd_to_local": 57.10},
        ]


def test_cache_miss_fetches_and_returns_rate(tmp_path):
    f = FakeFetcher()
    rate = get_mid_rate("MXN", "2026-03-13", cache_path=tmp_path / "c.csv", fetcher=f)
    assert rate == 17.85
    assert f.calls == ["2026-03-13"]


def test_second_call_uses_cache_not_api(tmp_path):
    f = FakeFetcher()
    path = tmp_path / "c.csv"
    get_mid_rate("MXN", "2026-03-13", cache_path=path, fetcher=f)
    get_mid_rate("MXN", "2026-03-13", cache_path=path, fetcher=f)
    assert len(f.calls) == 1


def test_one_fetch_caches_all_three_currencies(tmp_path):
    f = FakeFetcher()
    path = tmp_path / "c.csv"
    get_mid_rate("MXN", "2026-03-13", cache_path=path, fetcher=f)
    assert get_mid_rate("INR", "2026-03-13", cache_path=path, fetcher=f) == 86.50
    assert get_mid_rate("PHP", "2026-03-13", cache_path=path, fetcher=f) == 57.10
    assert len(f.calls) == 1


def test_weekend_date_uses_prior_business_day_rate(tmp_path):
    # 2026-03-14 is a Saturday. The API answers with Friday 2026-03-13's rate.
    f = FakeFetcher(rate_date_for={"2026-03-14": "2026-03-13"})
    path = tmp_path / "c.csv"
    rate = get_mid_rate("MXN", "2026-03-14", cache_path=path, fetcher=f)
    assert rate == 17.85
    cached = pd.read_csv(path, dtype=str)
    row = cached[(cached.requested_date == "2026-03-14") & (cached.currency == "MXN")].iloc[0]
    assert row.rate_date == "2026-03-13"   # the cache records which day was really used


def test_existing_cache_is_kept_when_new_dates_are_added(tmp_path):
    path = tmp_path / "c.csv"
    pd.DataFrame([{"requested_date": "2025-06-02", "rate_date": "2025-06-02",
                   "currency": "MXN", "usd_to_local": 19.4}]).to_csv(path, index=False)
    f = FakeFetcher()
    get_mid_rate("MXN", "2026-03-13", cache_path=path, fetcher=f)
    assert get_mid_rate("MXN", "2025-06-02", cache_path=path, fetcher=f) == 19.4
    assert len(pd.read_csv(path)) == 4   # 1 old row + 3 new rows


def test_unsupported_currency_raises(tmp_path):
    with pytest.raises(ValueError):
        get_mid_rate("GBP", "2026-03-13", cache_path=tmp_path / "c.csv", fetcher=FakeFetcher())


def test_bad_date_raises(tmp_path):
    with pytest.raises(ValueError):
        get_mid_rate("MXN", "03/13/2026", cache_path=tmp_path / "c.csv", fetcher=FakeFetcher())


def test_save_false_does_not_write_a_file(tmp_path):
    path = tmp_path / "c.csv"
    rate = get_mid_rate("MXN", "2026-03-13", cache_path=path, fetcher=FakeFetcher(), save=False)
    assert rate == 17.85
    assert not path.exists()
