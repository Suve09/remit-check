"""True Cost Engine: what a money transfer really costs.

Rates are local currency per US dollar. Percentages are stored as fractions
(0.063 means 6.3 percent), matching the formulas in the project brief.
"""

CASH_LIKE = {"cash", "money_order", "cashiers_check"}
NON_CASH = {"debit_card", "credit_card", "bank_account"}
EXCISE_RATE = 0.01

# How many transfers a year each survey answer means.
# few_per_year is NOT defined in the brief: 4 is an assumption. Document it in the methodology.
TRANSFERS_PER_YEAR = {"weekly": 52, "twice_monthly": 24, "monthly": 12, "few_per_year": 4}


def _is_missing(value):
    """True for None or NaN (a blank cell read by pandas)."""
    return value is None or value != value


def spread_pct(mid_rate, offered_rate):
    """Share of the amount lost because the offered rate is below the mid-market rate."""
    if mid_rate <= 0 or offered_rate <= 0:
        raise ValueError("Exchange rates must be greater than 0.")
    return (mid_rate - offered_rate) / mid_rate


def excise_tax(amount_usd, funding_method, tax_line_shown="no", tax_usd=None):
    """Return (tax in dollars, label). Label is 'reported', 'estimated', or 'none'."""
    if funding_method not in CASH_LIKE | NON_CASH:
        raise ValueError(f"Unknown funding method: {funding_method!r}")
    if tax_line_shown == "yes" and not _is_missing(tax_usd):
        return round(float(tax_usd), 2), "reported"       # receipt showed it: do not add it again
    if funding_method in CASH_LIKE:
        return round(EXCISE_RATE * amount_usd, 2), "estimated"
    return 0.0, "none"


def true_cost(amount_usd, fee_usd, offered_rate, mid_rate, funding_method,
              tax_line_shown="no", tax_usd=None):
    """Full cost of one transfer. Returns a dictionary of results."""
    if _is_missing(fee_usd):
        raise ValueError("fee_usd is missing.")
    if _is_missing(amount_usd) or amount_usd <= 0:
        raise ValueError("amount_usd must be greater than 0.")
    if fee_usd < 0:
        raise ValueError("fee_usd cannot be negative.")

    pct = spread_pct(mid_rate, offered_rate)
    spread_usd = round(amount_usd * pct, 2)
    tax, tax_label = excise_tax(amount_usd, funding_method, tax_line_shown, tax_usd)
    total_usd = round(fee_usd + spread_usd + tax, 2)

    return {
        "mid_rate": mid_rate,
        "spread_pct": round(pct, 4),
        "spread_usd": spread_usd,
        "excise_tax_usd": tax,
        "tax_label": tax_label,
        "total_cost_usd": total_usd,
        "total_cost_pct": round(total_usd / amount_usd, 4),
        "lost_local": round(amount_usd * (mid_rate - offered_rate), 2),
    }


def annual_cost(total_cost_usd, send_frequency):
    """Projected yearly cost from one transfer and how often the household sends."""
    if send_frequency not in TRANSFERS_PER_YEAR:
        raise ValueError(f"Unknown send frequency: {send_frequency!r}")
    return round(total_cost_usd * TRANSFERS_PER_YEAR[send_frequency], 2)


def gap_to_cheapest(total_cost_pct, rpw_cheapest_pct, amount_usd):
    """Dollars paid above the cheapest surveyed option. Both percentages are fractions."""
    return round((total_cost_pct - rpw_cheapest_pct) * amount_usd, 2)
