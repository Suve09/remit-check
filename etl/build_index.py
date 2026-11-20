"""Build the Community Corridor Price Index from survey rows.

Steps:  load -> keep only known columns -> validate -> add true cost -> group by
corridor / community area / quarter -> hide groups with fewer than 5 entries ->
add the World Bank benchmark -> save.

Run from the project folder:
    python etl/build_index.py data/demo_synthetic.csv
"""
import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from remitcheck.benchmark import corridor_benchmark, load_rpw
from remitcheck.cost import annual_cost, true_cost
from remitcheck.rates import get_mid_rate

MIN_N = 5  # privacy rule: a group with fewer than 5 entries is never published
ALL_AREAS = "All Chicago (any area)"
NOT_GIVEN = "Not given"

# Only these columns are ever read. Everything else (names, free text, device info...) is dropped.
KEEP = ["transfer_date", "destination_country", "destination_currency", "provider", "amount_usd",
        "fee_usd", "offered_rate", "received_local", "funding_method", "payout_method",
        "tax_line_shown", "tax_usd", "send_frequency", "community_area"]
CORRIDOR_CURRENCY = {"Mexico": "MXN", "India": "INR", "Philippines": "PHP"}
FUNDING = {"cash", "money_order", "cashiers_check", "debit_card", "credit_card", "bank_account"}
FREQUENCY = {"weekly", "twice_monthly", "monthly", "few_per_year"}
MAX_AMOUNT = 10_000
# "Far from mid-market": the receipt rate is more than 5% better or 25% worse than the real rate.
SPREAD_MIN, SPREAD_MAX = -0.05, 0.25


def quarter_label(d):
    return f"{d.year}_{(d.month - 1) // 3 + 1}Q"


def load_survey(path):
    df = pd.read_csv(path)
    is_synthetic = bool(len(df) and "is_synthetic" in df.columns
                        and df["is_synthetic"].astype(str).str.lower().eq("true").all())
    missing = [c for c in KEEP if c not in df.columns]
    if missing:
        raise ValueError(f"Survey file is missing columns: {missing}")
    return df[KEEP].copy(), is_synthetic


def validate_and_cost(df, mid_rate_fn):
    """Return (good_rows_with_costs, dict of how many rows were rejected for each reason)."""
    good, rejected = [], {}

    def reject(reason):
        rejected[reason] = rejected.get(reason, 0) + 1

    for r in df.to_dict("records"):
        try:
            day = pd.to_datetime(r["transfer_date"], errors="raise").date()
        except Exception:
            reject("bad date"); continue
        country, cur = r["destination_country"], r["destination_currency"]
        if country not in CORRIDOR_CURRENCY or CORRIDOR_CURRENCY[country] != cur:
            reject("not a launch corridor"); continue
        if r["funding_method"] not in FUNDING:
            reject("unknown funding method"); continue
        if r["send_frequency"] not in FREQUENCY:
            reject("unknown send frequency"); continue
        try:
            amount, fee, offered = float(r["amount_usd"]), float(r["fee_usd"]), float(r["offered_rate"])
        except (TypeError, ValueError):
            reject("missing number"); continue
        if not (0 < amount <= MAX_AMOUNT):
            reject("amount out of range"); continue
        if fee < 0:
            reject("negative fee"); continue
        if offered <= 0:
            reject("bad exchange rate"); continue
        tax = None if pd.isna(r["tax_usd"]) or r["tax_usd"] == "" else float(r["tax_usd"])
        try:
            mid = mid_rate_fn(cur, day.isoformat())
            res = true_cost(amount, fee, offered, mid, r["funding_method"], str(r["tax_line_shown"]), tax)
        except Exception:
            reject("could not compute cost"); continue
        if not (SPREAD_MIN <= res["spread_pct"] <= SPREAD_MAX):
            reject("rate far from mid-market"); continue

        area = r["community_area"]
        area = NOT_GIVEN if pd.isna(area) or str(area).strip() in ("", "prefer not to say") else str(area).strip()
        good.append({
            "destination_country": country,
            "community_area": area,
            "quarter": quarter_label(day),
            "total_cost_pct": res["total_cost_pct"] * 100,  # percent, same units as World Bank
            "total_cost_usd": res["total_cost_usd"],
            "annual_cost_usd": annual_cost(res["total_cost_usd"], r["send_frequency"]),
        })
    return pd.DataFrame(good), rejected


def aggregate(costed):
    """Medians by corridor and quarter, for each community area and for all of Chicago."""
    if costed.empty:
        return pd.DataFrame(columns=["destination_country", "community_area", "quarter", "n",
                                     "median_cost_pct", "median_cost_usd", "median_annual_cost_usd"])
    by_area = costed[costed["community_area"] != NOT_GIVEN]
    whole = costed.assign(community_area=ALL_AREAS)  # includes people who skipped the neighborhood question
    parts = []
    for frame in (by_area, whole):
        g = frame.groupby(["destination_country", "community_area", "quarter"])
        parts.append(g.agg(n=("total_cost_pct", "size"),
                           median_cost_pct=("total_cost_pct", "median"),
                           median_cost_usd=("total_cost_usd", "median"),
                           median_annual_cost_usd=("annual_cost_usd", "median")).reset_index())
    return pd.concat(parts, ignore_index=True)


def suppress(cells, min_n=MIN_N):
    """Drop every group with fewer than min_n entries. Returns (kept, number_dropped)."""
    keep = cells["n"] >= min_n
    return cells[keep].copy(), int((~keep).sum())


def build_index(survey, mid_rate_fn, rpw, min_n=MIN_N):
    costed, rejected = validate_and_cost(survey, mid_rate_fn)
    cells = aggregate(costed)
    published, n_suppressed = suppress(cells, min_n)
    bench = corridor_benchmark(rpw)
    out = published.merge(bench, on="destination_country", how="left")
    out["gap_to_rpw_median_pct"] = out["median_cost_pct"] - out["rpw_corridor_median_pct"]
    for col in ("median_cost_pct", "median_cost_usd", "median_annual_cost_usd", "gap_to_rpw_median_pct"):
        out[col] = out[col].round(2)
    out = out.sort_values(["destination_country", "community_area", "quarter"]).reset_index(drop=True)
    meta = {
        "rows_in": int(len(survey)),
        "rows_used": int(len(costed)),
        "rows_rejected": rejected,
        "cells_before_suppression": int(len(cells)),
        "cells_suppressed": n_suppressed,
        "cells_published": int(len(out)),
        "min_entries_per_cell": min_n,
        "rpw_period": str(bench["rpw_period"].iloc[0]),
    }
    return out, meta


def main(argv):
    survey_path = argv[1] if len(argv) > 1 else "data/demo_synthetic.csv"
    rpw_path = argv[2] if len(argv) > 2 else "data/rpw_from_2016.csv"
    survey, is_synthetic = load_survey(survey_path)
    rpw = load_rpw(rpw_path)

    index, meta = build_index(survey, lambda cur, day: get_mid_rate(cur, day), rpw)

    # A synthetic run can never overwrite or be mistaken for the real index.
    out_path = "data/index_demo_synthetic.csv" if is_synthetic else "data/index_v1.csv"
    index["is_synthetic"] = is_synthetic
    index.to_csv(out_path, index=False)
    meta.update({"is_synthetic": is_synthetic, "source_file": os.path.basename(survey_path),
                 "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    with open(out_path.replace(".csv", "_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"Wrote {out_path}")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main(sys.argv)
