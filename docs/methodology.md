# Methodology: Remit Check and the Community Corridor Price Index

Version 1 (preliminary), November 2026. Prepared for the Chicago Education Advocacy Cooperative (ChiEAC).

Remit Check reports what money transfers cost. It does not accuse any provider of wrongdoing, rank providers as good or bad, or give financial advice.

## 1. What we measure

**True cost of a transfer** = fee + exchange-rate spread + tax, measured against the amount sent.

| Part | Definition |
|---|---|
| Fee | The fee shown on the receipt, in US dollars. |
| Exchange-rate spread | The gap between the rate the sender was given and the mid-market rate on the transfer date. Spread % = (mid rate - offered rate) / mid rate. Spread in dollars = amount sent x spread %. |
| Tax | The 1% federal excise tax on transfers funded with cash, a money order, or a cashier's check (in effect since January 1, 2026). Transfers funded by bank account, debit card, or credit card carry no tax. |
| Total cost % | Total cost in dollars divided by the amount sent. |

Amounts are in US dollars. All exchange rates are local currency per US dollar. Each part is rounded to the cent.

**Worked example.** A $300 cash transfer to Mexico, fee $4.99, offered rate 17.20, mid rate 17.85: spread 3.64% ($10.92), tax $3.00, total cost $18.91 (6.30%). This case is a unit test.

## 2. Exchange-rate rules

- **Mid-market rate** comes from European Central Bank (ECB) euro reference rates through the Frankfurter API. The US dollar rate for a currency is (EUR to local currency) divided by (EUR to US dollar).
- **Weekends and holidays.** The ECB does not publish on those days. The rate from the most recent business day is used, and the date actually used is stored with the rate.
- **Cross-check.** For the Mexican peso and Indian rupee, rates are spot-checked against Federal Reserve H.10 data with a 0.3% tolerance. The Fed does not publish a Philippine peso rate, so that corridor has no cross-check.
- The ECB rate is a reference rate published once a day. It is not a live market quote.

## 3. Tax rules

- If the receipt shows the 1% tax as its own line, the reported amount is used and is not added a second time.
- If the receipt does not show it, or the sender is not sure, and the transfer was funded with cash, a money order, or a cashier's check, the tax is calculated as 1% of the amount sent and labeled "estimated."

## 4. Data sources

**Community entries.** Anonymous, voluntary survey responses (English and Spanish) entered from the sender's own receipt. The survey asks for no names, phone numbers, email addresses, street addresses, account numbers, or immigration status. Neighborhood is a Chicago community area chosen from a drop-down list, with "prefer not to say" available.

**World Bank benchmark.** Remittance Prices Worldwide (RPW), latest quarter in the file (2025 Q3). We use the US-to-Mexico, US-to-India, and US-to-Philippines rows.

## 5. How the index is built

1. **Load** the survey export. Only the 14 columns in the data dictionary are read. Anything else, including free text, is dropped.
2. **Validate.** Rows are rejected if the fee is negative, the amount is zero or above $10,000, the destination is not one of the three launch corridors, the payment method or send frequency is unknown, or the exchange rate is far from the mid-market rate (more than 5% better or more than 25% worse). The number of rejected rows and the reason are saved in the output metadata.
3. **Compute** the true cost of each remaining row with the same engine used by the app.
4. **Aggregate.** For each corridor, community area, and quarter we report the number of entries (n), the median total cost %, the median total cost in dollars, and the median annual cost. A second row per corridor and quarter covers all of Chicago, including entries where the sender chose not to give a neighborhood.
5. **Suppress** (see section 6).
6. **Join the benchmark** (see section 7).

**Why medians.** A few unusually high or low receipts can pull an average far from what a typical sender pays. The median is the middle value, so it is less affected by outliers.

**Annual cost** = total cost per transfer x transfers per year, using the sender's stated frequency: weekly 52, twice a month 24, monthly 12. "A few times a year" is not defined in the project brief, so we assume **4**. This is an assumption, and it is the one most likely to be changed.

**Quarter** is the calendar quarter of the transfer date (for example, 2026_4Q).

## 6. Privacy and suppression

- **Minimum cell size of 5.** Any corridor, community area, and quarter group with fewer than 5 entries is removed from the published index. The number of removed groups is recorded in the metadata.
- Suppressed entries still count toward the all-Chicago row for their corridor and quarter.
- **Only aggregates are published.** Row-level data is never published, even with names removed.
- Survey exports are kept out of the public repository.
- The calculator processes what a user types in memory and does not store it.

Suppression lowers the risk that a person could be identified but does not remove it. For very small neighborhoods, even larger groups can in principle reveal something about a small community.

## 7. World Bank benchmark

Each published row carries the World Bank median and cheapest total cost for its corridor, next to the community median. The gap is the community median minus the World Bank median, in percentage points.

- The benchmark is **per corridor**. It is not matched to the payment method or payout method of the community entries.
- RPW prices are for a **$200** transfer. Community transfers vary in size, and the percentage cost of a transfer usually changes with the amount.
- The **median** is used. It is not thrown off by outliers such as the flat 17.5% shown for one bank in every corridor.
- The **cheapest** figure ignores negative totals. Some RPW rows are negative because of negative margins, and they are not real prices.
- RPW is a national survey of listed services. The community figures are what senders actually paid. The two are not measuring the same thing, so differences should be read as context, not as a score.

## 8. Limitations

- **Not a random sample.** Entries come from people who chose to take the survey. They may not represent all senders in Chicago.
- **Self-reported.** Senders type what their receipt says. We cannot check it.
- **Small numbers.** Early quarters will have few entries per neighborhood, so many groups will be suppressed.
- **Three corridors only.** Mexico, India, and the Philippines.
- **Rates.** The ECB reference rate is a daily rate and can differ from the exact market rate at the minute of a transfer.
- **Prices change.** Provider fees and margins change often. The index describes a past quarter.
- **Synthetic demo data.** Any file with "synthetic" in its name contains invented rows made only for testing and demos. It says nothing about real prices.

## 9. Sponsor-neutrality rule

*Draft for ChiEAC to confirm.*

- Sponsors do not choose, change, or remove data, methods, or findings.
- Every provider is measured the same way. No provider, sponsor, or sponsor's competitor gets different treatment.
- Remit Check does not endorse any provider, bank, credit union, or product. Sponsor logos and messages appear apart from the data and are labeled as sponsorship.
- The methodology and suppression rules are published and apply to every edition, including any branded edition.
- Wording stays factual and neutral: it reports costs and does not accuse anyone or give financial advice.

## 10. Reproducing the index

The code is in this repository.

- `etl/build_index.py` builds the index from a survey CSV.
- `remitcheck/cost.py` is the cost engine, with its tests in `tests/`.
- `remitcheck/rates.py` fetches and caches exchange rates.
- `remitcheck/benchmark.py` builds the World Bank benchmark.
- `docs/data_dictionary.md` lists every field.
