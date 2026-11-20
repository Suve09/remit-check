"""World Bank Remittance Prices Worldwide (RPW) benchmark for each launch corridor.

The RPW file lists one row per provider, payment instrument and pickup method.
Here we boil it down to ONE benchmark per corridor for the latest quarter:
the median and the cheapest total cost (%) for sending the $200 example.
"""
import pandas as pd

CORRIDORS = ["Mexico", "India", "Philippines"]
USECOLS = ["period", "source_name", "destination_name", "firm",
           "payment instrument", "pickup method", "cc1 total cost %"]


def load_rpw(path):
    """Read the RPW file (the .csv saved from the 'Dataset (from Q2 2016)' sheet, or the .xlsx itself)."""
    if str(path).lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(path, sheet_name="Dataset (from Q2 2016)")
    else:
        df = pd.read_csv(path, low_memory=False)
    return df[USECOLS].copy()


def corridor_benchmark(rpw, period=None):
    """One row per corridor: rpw_corridor_median_pct, rpw_cheapest_pct, rpw_n_services, rpw_period.

    period=None uses the latest quarter in the file (periods look like 2025_3Q).
    The cheapest figure ignores negative totals, which come from negative margins and are not real prices
    (see docs/methodology.md). The median is not thrown off by outliers such as the flat 17.5% Citibank rows.
    """
    d = rpw[(rpw["source_name"] == "United States") & (rpw["destination_name"].isin(CORRIDORS))].copy()
    d["cost"] = pd.to_numeric(d["cc1 total cost %"], errors="coerce")
    d = d.dropna(subset=["cost"])
    if period is None:
        period = max(d["period"].astype(str))
    d = d[d["period"].astype(str) == str(period)]
    if d.empty:
        raise ValueError(f"No US-to-{CORRIDORS} rows found for period {period!r}.")

    rows = []
    for country, g in d.groupby("destination_name"):
        nonneg = g.loc[g["cost"] >= 0, "cost"]
        rows.append({
            "destination_country": country,
            "rpw_corridor_median_pct": round(float(g["cost"].median()), 2),
            "rpw_cheapest_pct": round(float(nonneg.min()), 2),
            "rpw_n_services": int(len(g)),
            "rpw_period": str(period),
        })
    return pd.DataFrame(rows)
