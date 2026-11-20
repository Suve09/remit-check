"""Make data/demo_synthetic.csv: about 200 INVENTED survey rows for demos and tests.

Every row is fake. The file is named 'synthetic' and every row has
is_synthetic = True so it can never be mistaken for real community data.
Run from the project folder:  python etl/make_synthetic.py
"""
import os
import random
from datetime import date, timedelta

import pandas as pd

random.seed(2026)  # same seed = same file every time

N_ROWS = 200

# Rough mid-market rates (local currency per USD). Approximate on purpose: this is fake data.
CORRIDORS = {
    "Mexico": {"currency": "MXN", "mid": 18.6, "weight": 0.60},
    "India": {"currency": "INR", "mid": 88.0, "weight": 0.22},
    "Philippines": {"currency": "PHP", "mid": 58.0, "weight": 0.18},
}

# provider: (typical fee in dollars, typical exchange-rate margin as a fraction)
PROVIDERS = {
    "Western Union": (5.0, 0.040),
    "MoneyGram": (4.5, 0.035),
    "Ria": (3.5, 0.025),
    "Remitly": (2.0, 0.015),
    "Wise": (2.5, 0.005),
    "Xoom": (4.0, 0.030),
}

# Chicago community areas, with a weight so a few areas get many entries and a few get very few.
# The rare ones (weight 1) are there on purpose so the privacy rule (hide groups under 5) has something to hide.
AREAS = {
    "South Lawndale": 14, "Brighton Park": 10, "Gage Park": 9, "Archer Heights": 8,
    "Belmont Cragin": 8, "Albany Park": 8, "West Ridge": 7, "Avondale": 6,
    "Chicago Lawn": 6, "Hermosa": 5, "Portage Park": 5, "Rogers Park": 5,
    "Lower West Side": 3, "Edgewater": 1, "Norwood Park": 1,
}

FREQUENCIES = ["weekly", "twice_monthly", "monthly", "few_per_year"]
FREQ_WEIGHTS = [0.10, 0.30, 0.45, 0.15]


def pick(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


rows = []
for _ in range(N_ROWS):
    country = pick(list(CORRIDORS), [c["weight"] for c in CORRIDORS.values()])
    info = CORRIDORS[country]
    provider = pick(list(PROVIDERS), [3, 2, 2, 3, 1, 1])
    fee_typ, margin_typ = PROVIDERS[provider]

    amount = random.choice([100, 150, 200, 200, 250, 300, 300, 400, 500, 600])
    fee = round(max(0, random.gauss(fee_typ, 0.8)), 2)
    margin = max(0.0, random.gauss(margin_typ, 0.008))
    offered = round(info["mid"] * (1 - margin), 4)

    # Cash is common for Mexico, less common elsewhere.
    cash_share = 0.55 if country == "Mexico" else 0.25
    funding = pick(["cash", "debit_card", "bank_account", "credit_card"],
                   [cash_share, 0.30, 0.90 - cash_share, 0.10])
    if provider == "Wise":
        funding = pick(["bank_account", "debit_card"], [0.6, 0.4])
    payout = pick(["bank_deposit", "cash_pickup", "mobile_wallet"],
                  [0.45, 0.45, 0.10] if country == "Mexico" else [0.65, 0.20, 0.15])

    # Some receipts show the 1% tax as its own line; if so, record the amount.
    tax_shown, tax_usd = "no", ""
    if funding == "cash":
        tax_shown = pick(["yes", "no", "unsure"], [0.35, 0.40, 0.25])
        if tax_shown == "yes":
            tax_usd = round(0.01 * amount, 2)

    when = date(2026, 10, 1) + timedelta(days=random.randint(0, 40))
    rows.append({
        "transfer_date": when.isoformat(),
        "destination_country": country,
        "destination_currency": info["currency"],
        "provider": provider,
        "amount_usd": float(amount),
        "fee_usd": fee,
        "offered_rate": offered,
        "received_local": round(amount * offered, 2),
        "funding_method": funding,
        "payout_method": payout,
        "tax_line_shown": tax_shown,
        "tax_usd": tax_usd,
        "send_frequency": pick(FREQUENCIES, FREQ_WEIGHTS),
        "community_area": pick(list(AREAS), list(AREAS.values())),
        "is_synthetic": True,
    })

df = pd.DataFrame(rows)
os.makedirs("data", exist_ok=True)
df.to_csv("data/demo_synthetic.csv", index=False)

print("rows:", len(df))
print(df["destination_country"].value_counts().to_string())
print("areas with fewer than 5 rows:", int((df["community_area"].value_counts() < 5).sum()))
