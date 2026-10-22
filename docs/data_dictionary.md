Data Dictionary (v1)

Project: remit-check Last updated: Week 1 (October 19-23 2026)

All rates are expressed as units of local currency per US dollar. Amounts are in US dollars unless stated.

1. Survey fields (anonymous, bilingual)

The survey asks no names, phone numbers, addresses, account numbers, or immigration status. Consent text is shown first, in English and Spanish.

#	Field	Type	Allowed values	Maps to CSV column
1	Destination country	Drop-down	Mexico, India, Philippines, other	destination_country
2	Provider	Drop-down + "other" text	Common providers, other	provider
3	Transfer date	Date	ISO date	transfer_date
4	Amount sent (USD, before fee)	Number	> 0 and <= 10,000	amount_usd
5	Fee charged (USD)	Number	>= 0	fee_usd
6	Exchange rate on receipt	Number	> 0	offered_rate
7	Amount received (local currency), optional	Number	> 0 or blank	received_local
8	How the sender paid	Drop-down	Cash, money order, debit card, credit card, bank account	funding_method
9	How the money was received	Drop-down	Cash pickup, bank deposit, mobile wallet, home delivery	payout_method
10	Receipt shows the 1% federal tax as its own line	Yes / No / Not sure	yes, no, unsure	tax_line_shown
11	How often the sender sends money	Drop-down	Weekly, twice a month, monthly, a few times a year	send_frequency
12	Chicago neighborhood	Drop-down	77 community areas + "prefer not to say"	community_area
2. CSV template columns (data/template.csv)
Column	Type	Example	Allowed values / rules
transfer_date	date	2026-03-14	ISO format (YYYY-MM-DD)
destination_country	text	Mexico	Must match a launch corridor: Mexico, India, Philippines
destination_currency	text	MXN	ISO 4217 code (MXN, INR, PHP)
provider	text	Western Union	Free text; normalized by the engine
amount_usd	number	300.00	Amount paid to send, before fee. Reject <= 0 or > 10,000
fee_usd	number	4.99	Fee as shown on receipt. Reject negative
offered_rate	number	17.20	Local currency per USD. Reject if far from mid-market
received_local	number	5160	Optional. Used to cross-check offered_rate
funding_method	text	cash	cash, money_order, cashiers_check, debit_card, credit_card, bank_account
payout_method	text	cash_pickup	cash_pickup, bank_deposit, mobile_wallet, home_delivery
tax_line_shown	text	no	yes, no, unsure
tax_usd	number	(blank)	Fill only if tax_line_shown is yes
send_frequency	text	twice_monthly	weekly, twice_monthly, monthly, few_per_year
community_area	text	South Lawndale	One of the 77 Chicago community areas, or blank

Free-text columns are dropped by the ETL. No column holds a name, address, phone, or account number.

3. Computed fields (added by the engine on output)
Field	Formula
mid_rate	ECB cross rate for the transfer date: (EUR/local) / (EUR/USD). Weekend or holiday uses the most recent prior business day
spread_pct	(mid_rate - offered_rate) / mid_rate
spread_usd	amount_usd * spread_pct
excise_tax_usd	0.01 * amount_usd if funding_method is cash, money_order, or cashiers_check; 0 if bank_account, debit_card, or credit_card. If tax_line_shown is yes, use tax_usd and do not add it again
total_cost_usd	fee_usd + spread_usd + excise_tax_usd
total_cost_pct	total_cost_usd / amount_usd
lost_local	amount_usd * (mid_rate - offered_rate)
annual_cost_usd	Sum of total_cost_usd over the last 12 months, or total_cost_usd * transfers_per_year (projection)
rpw_corridor_avg_pct	World Bank RPW average total cost % for the corridor
rpw_cheapest_pct	World Bank RPW lowest total cost % for the corridor
gap_to_cheapest_usd	(total_cost_pct - rpw_cheapest_pct) * amount_usd

Computed tax is labeled "estimated" in app output.

transfers_per_year by send_frequency: weekly = 52, twice_monthly = 24, monthly = 12, few_per_year = TBD (not defined in the brief; choose a value and document it in the methodology note).

Worked example (first unit test): $300 cash to Mexico, fee $4.99, offered rate 17.20, mid rate 17.85. Spread 3.64%, spread $10.92, tax $3.00, total cost $18.91 (6.30%), 195 pesos lost, annual cost at 24 transfers $453.84.

4. World Bank RPW dataset

Source: Remittance Prices Worldwide, file rpw_dataset_2011_2025_q3.xlsx, sheet Dataset (from Q2 2016). Latest quarter in file: 2025_3Q.

Column	Meaning
period	Quarter, format YYYY_nQ (e.g., 2025_3Q). Note: 2025_2Q is not in the file
source_name	Sending country (filter: United States)
destination_name	Receiving country (filter: Mexico, India, Philippines)
firm	Provider name (needs normalization, see below)
firm_type	Provider type
payment instrument	How the sender pays (cash, debit card, credit card, bank account)
pickup method	How the money is received
cc1 lcu fee	Fee for the $200 transfer
cc1 fx margin	Exchange-rate margin (%) for the $200 transfer
cc1 total cost %	Total cost (%) for the $200 transfer
transparent	Whether the provider discloses the cost clearly

cc1 = the $200 transfer. cc2 = the $500 transfer.

Latest quarter, US to the three corridors: 150 rows (India 46, Mexico 46, Philippines 58).

Notes:

Each row is one provider with one payment instrument and one pickup method. Benchmark by corridor, payment instrument, and pickup method, not by provider alone.
Negative totals exist (e.g., Walmart2World debit-card rows) because of negative margins. Flag them in the methodology note.
Citibank shows 17.5% for $200 in all three corridors (flat $35 fee). Treat as an outlier.
Provider name variants to normalize
Variants found	Normalized name
Transferwise, Wise	Wise
Transfast, Trans-Fast	Transfast
Casa de Cambio Delgado, Casa de cambio Delgado, Delgado Travel	Casa de Cambio Delgado
Dahabshiil, Dahabshil	Dahabshiil
Small World, Small World FS-Choice, Small World FS-LCC	Small World
Remit2India, money2India (ICICI Bank)	Remit2India
AisRemesasCuba.com (trailing space)	AisRemesasCuba.com

Rule: lowercase, strip spaces and punctuation, then map through an alias table. User-entered providers not in RPW are kept as typed and get no RPW benchmark.

5. Exchange-rate cache (data/rates_cache.csv)

Source: Frankfurter API (ECB euro reference rates), base EUR. USD cross rate = (EUR to local) / (EUR to USD).

Column	Meaning
requested_date	Date asked for
rate_date	Date the API actually used (prior business day if the requested date was a weekend or holiday)
currency	MXN, INR, or PHP
usd_to_local	Local currency per US dollar, 4 decimals
Cross-check against Federal Reserve H.10

Tolerance: 0.3%. Differences above 0.3% are noted here.

Date	Currency	ECB cross rate	Fed H.10	Difference	Result
2025-06-02	MXN	(19.2719)	(19.2450)	(0.0269)	(0.140%)
2025-06-02	INR	(85.3836)	(85.3300)	(0.0536)	(0.063%)

The Fed does not publish PHP, so there is no cross-check for the Philippines.

6. Privacy rules for all data
Never collect names, phone numbers, emails, street addresses, account or transaction numbers, receipt images, or immigration status.
Respondent email, IP, and device logging are turned off in the survey tool.
Public index outputs hide any group with fewer than 5 entries.
Uploaded CSVs are processed in memory and not stored.
