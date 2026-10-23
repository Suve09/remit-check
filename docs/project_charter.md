Project Charter: Remit Check

Organization: Chicago Education Advocacy Cooperative (ChiEAC) Fellow: Suvekshya Neupane Supervisor: Dr. Benjamin M. Drury Window: October 19 to December 4, 2026 (contingency week ending December 11) Repo: https://github.com/Suve09/remit-check

Problem

Immigrant households in Chicago send billions of dollars home each year and rarely know what a transfer really costs. The fee on the receipt is only part of the price. Most of the cost is usually hidden in the exchange rate, and since January 1, 2026, cash-funded transfers also carry a 1 percent federal excise tax. The World Bank publishes corridor-level prices nationally, but nobody publishes what transfers actually cost at the Chicago neighborhood level.

Solution

Remit Check is a free, bilingual (English and Spanish) web tool. A sender types in what their receipt already shows, and the tool reports:

the true cost of each transfer against the mid-market exchange rate (fee + exchange-rate spread + tax),
what the household pays over a year,
how their provider compares with others on the same corridor, using World Bank Remittance Prices Worldwide data.

Anonymous, aggregated entries feed a public Community Corridor Price Index by Chicago community area.

Users
Senders: Chicago households sending money abroad, especially cash-paying and unbanked senders.
Community navigators and service organizations: staff who help many clients and upload receipts in bulk.
ChiEAC and future sponsors: credit unions, CDFIs, and immigrant-service organizations that would sponsor the index or a branded edition.
Launch corridors

United States to Mexico (MXN), India (INR), and the Philippines (PHP). All three are large Chicago sending communities, are covered by the World Bank dataset, and have exchange rates in the free ECB feed. A fourth corridor is added only if the project is ahead of schedule at the end of Week 5.

Deliverables
Bilingual anonymous survey and CSV template
True Cost Engine in Python with a tested pytest suite
Streamlit app (four pages, English and Spanish toggle)
Community Corridor Price Index with written methodology
Public Tableau dashboard
Revenue kit for ChiEAC (sponsor one-pager, sample report, embed instructions, prospect list, demo video)
Final report, handoff README, and 30-minute demo
Success metrics
Three corridors live and tested end to end.
At least 10 passing pytest tests, including the worked example (a $300 cash transfer to Mexico costs $18.91, or 6.30 percent).
App deployed with four pages and no stored uploads.
Index published with the World Bank benchmark joined and every cell with fewer than 5 entries suppressed.
Public dashboard with four views, linked from the app and the README.
Revenue kit delivered, including a 15-organization prospect list.
Seven weekly LinkedIn posts plus one capstone post, each tagging ChiEAC and Benjamin Drury.
Out of scope

Scraping provider sites, user accounts or stored entries, live or intraday exchange rates, a native mobile app or custom front end, receipt photo upload and OCR, financial advice or provider endorsements, and more than three corridors before Week 6.

Guardrails
No names, phone numbers, email addresses, street addresses, account numbers, receipt images, or immigration status are collected.
Neighborhood is captured only as a Chicago community area from a drop-down list, with "prefer not to say" available.
Uploads are processed in memory and never stored.
Only aggregates are published, and every provider is compared on the same basis.
Wording is neutral: Remit Check reports costs and does not give financial advice.
Key data sources

World Bank Remittance Prices Worldwide, ECB reference rates via the Frankfurter API (cross-checked against Federal Reserve H.10), CFPB Remittance Transfer Rule, and City of Chicago community area boundaries.

Schedule
Week	Dates	Focus
1	Oct 19 to 23	Foundations: scope, tooling, data dictionary
2	Oct 26 to 30	Survey and CSV template
3	Nov 2 to 6	True Cost Engine and tests
4	Nov 9 to 13	Streamlit app
5	Nov 16 to 20	Community Corridor Price Index
6	Nov 23 to 27	Public dashboard
7	Nov 30 to Dec 4	Revenue kit and handoff
