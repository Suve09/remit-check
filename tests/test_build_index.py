import pandas as pd
import pytest

from etl.build_index import (ALL_AREAS, KEEP, build_index, quarter_label, suppress, validate_and_cost)
from remitcheck.benchmark import corridor_benchmark

MIDS = {"MXN": 17.85, "INR": 88.0, "PHP": 58.0}


def fake_mid(cur, day):
    return MIDS[cur]


def row(**kw):
    base = dict(transfer_date="2026-10-15", destination_country="Mexico", destination_currency="MXN",
                provider="Ria", amount_usd=300.0, fee_usd=4.99, offered_rate=17.20, received_local=5160.0,
                funding_method="cash", payout_method="cash_pickup", tax_line_shown="no", tax_usd="",
                send_frequency="twice_monthly", community_area="South Lawndale")
    base.update(kw)
    return base


def survey(rows):
    return pd.DataFrame(rows)[KEEP]


RPW = pd.DataFrame({
    "period": ["2025_3Q"] * 4 + ["2025_1Q"],
    "source_name": ["United States"] * 5,
    "destination_name": ["Mexico", "Mexico", "Mexico", "India", "Mexico"],
    "firm": list("abcde"),
    "payment instrument": ["Cash"] * 5,
    "pickup method": ["Cash"] * 5,
    "cc1 total cost %": [4.0, 6.0, -1.0, 3.0, 99.0],
})


def test_quarter_label():
    assert quarter_label(pd.Timestamp("2026-10-15")) == "2026_4Q"
    assert quarter_label(pd.Timestamp("2026-03-31")) == "2026_1Q"


def test_worked_example_row_is_costed():
    good, rejected = validate_and_cost(survey([row(offered_rate=17.20)]), fake_mid)
    assert rejected == {}
    assert good.loc[0, "total_cost_usd"] == pytest.approx(18.91, abs=0.02)
    assert good.loc[0, "total_cost_pct"] == pytest.approx(6.30, abs=0.05)


def test_bad_rows_are_rejected_with_reasons():
    rows = [row(fee_usd=-1), row(amount_usd=20000), row(offered_rate=5.0), row(funding_method="bitcoin"),
            row(destination_country="Guatemala", destination_currency="GTQ"), row()]
    good, rejected = validate_and_cost(survey(rows), fake_mid)
    assert len(good) == 1
    assert rejected == {"negative fee": 1, "amount out of range": 1, "rate far from mid-market": 1,
                        "unknown funding method": 1, "not a launch corridor": 1}


def test_suppress_hides_groups_under_five():
    cells = pd.DataFrame({"n": [4, 5, 12]})
    kept, dropped = suppress(cells)
    assert list(kept["n"]) == [5, 12] and dropped == 1


def test_small_area_is_never_published_but_counts_toward_all_chicago():
    rows = [row(community_area="Brighton Park") for _ in range(5)] + [row(community_area="Edgewater") for _ in range(2)]
    index, meta = build_index(survey(rows), fake_mid, RPW)
    areas = set(index["community_area"])
    assert "Brighton Park" in areas and "Edgewater" not in areas
    assert index.loc[index["community_area"] == ALL_AREAS, "n"].iloc[0] == 7
    assert meta["cells_suppressed"] == 1


def test_prefer_not_to_say_only_in_all_chicago():
    rows = [row(community_area="prefer not to say") for _ in range(6)]
    index, _ = build_index(survey(rows), fake_mid, RPW)
    assert list(index["community_area"]) == [ALL_AREAS]


def test_benchmark_uses_latest_quarter_and_ignores_negative_for_cheapest():
    b = corridor_benchmark(RPW).set_index("destination_country")
    assert b.loc["Mexico", "rpw_corridor_median_pct"] == 4.0
    assert b.loc["Mexico", "rpw_cheapest_pct"] == 4.0
    assert b.loc["Mexico", "rpw_period"] == "2025_3Q"
    assert b.loc["India", "rpw_n_services"] == 1


def test_index_carries_benchmark_and_gap():
    rows = [row() for _ in range(5)]
    index, _ = build_index(survey(rows), fake_mid, RPW)
    r = index.iloc[0]
    assert r["rpw_corridor_median_pct"] == 4.0
    assert r["gap_to_rpw_median_pct"] == pytest.approx(r["median_cost_pct"] - 4.0, abs=0.01)
