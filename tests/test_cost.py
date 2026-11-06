import pytest
from remitcheck.cost import true_cost, annual_cost, gap_to_cheapest, excise_tax

# Worked example from the brief: $300 cash to Mexico, fee 4.99, offered 17.20, mid 17.85.
EX = dict(amount_usd=300, fee_usd=4.99, offered_rate=17.20, mid_rate=17.85)


def test_worked_example_cash():
    r = true_cost(**EX, funding_method="cash")
    assert r["spread_pct"] == pytest.approx(0.0364, abs=1e-4)
    assert r["spread_usd"] == 10.92
    assert r["excise_tax_usd"] == 3.00
    assert r["total_cost_usd"] == 18.91
    assert r["total_cost_pct"] == pytest.approx(0.0630, abs=1e-4)
    assert r["lost_local"] == 195.00


def test_worked_example_annual():
    r = true_cost(**EX, funding_method="cash")
    assert annual_cost(r["total_cost_usd"], "twice_monthly") == 453.84


def test_debit_card_avoids_tax():
    r = true_cost(**EX, funding_method="debit_card")
    assert r["excise_tax_usd"] == 0.0
    assert r["total_cost_usd"] == 15.91
    assert r["total_cost_pct"] == pytest.approx(0.0530, abs=1e-4)


def test_switching_to_debit_saves_72_a_year():
    cash = true_cost(**EX, funding_method="cash")["total_cost_usd"]
    debit = true_cost(**EX, funding_method="debit_card")["total_cost_usd"]
    assert annual_cost(cash, "twice_monthly") - annual_cost(debit, "twice_monthly") == 72.00


@pytest.mark.parametrize("method", ["cash", "money_order", "cashiers_check"])
def test_cash_like_methods_are_taxed(method):
    assert excise_tax(300, method)[0] == 3.00


@pytest.mark.parametrize("method", ["debit_card", "credit_card", "bank_account"])
def test_non_cash_methods_not_taxed(method):
    assert excise_tax(300, method) == (0.0, "none")


def test_tax_on_receipt_is_not_added_twice():
    r = true_cost(**EX, funding_method="cash", tax_line_shown="yes", tax_usd=3.00)
    assert r["excise_tax_usd"] == 3.00
    assert r["tax_label"] == "reported"
    assert r["total_cost_usd"] == 18.91


def test_tax_unsure_uses_labeled_estimate():
    r = true_cost(**EX, funding_method="cash", tax_line_shown="unsure")
    assert r["tax_label"] == "estimated"


def test_zero_fee_can_still_cost_money():
    r = true_cost(amount_usd=200, fee_usd=0, offered_rate=17.00, mid_rate=17.85,
                  funding_method="bank_account")
    assert r["total_cost_usd"] == 9.52   # the 'zero fee' transfer still loses money in the rate


def test_missing_fee_raises():
    with pytest.raises(ValueError):
        true_cost(amount_usd=300, fee_usd=None, offered_rate=17.20, mid_rate=17.85,
                  funding_method="cash")


def test_nan_fee_from_pandas_raises():
    with pytest.raises(ValueError):
        true_cost(amount_usd=300, fee_usd=float("nan"), offered_rate=17.20, mid_rate=17.85,
                  funding_method="cash")


def test_unknown_funding_method_raises():
    with pytest.raises(ValueError):
        true_cost(**EX, funding_method="bitcoin")


def test_zero_amount_raises():
    with pytest.raises(ValueError):
        true_cost(amount_usd=0, fee_usd=4.99, offered_rate=17.20, mid_rate=17.85,
                  funding_method="cash")


def test_weekly_projection():
    assert annual_cost(10.00, "weekly") == 520.00


def test_gap_to_cheapest():
    # 6.30% paid vs 2.00% cheapest on a $300 transfer = about $12.90 more
    assert gap_to_cheapest(0.0630, 0.02, 300) == 12.90
