# remit-check

A free, bilingual (English/Spanish) tool that shows the real cost of sending money home, plus a community price index for Chicago neighborhoods.

Providers often hide most of the cost in the exchange rate, not the listed fee. Starting in 2026, cash-funded transfers also carry a 1% federal remittance excise tax. remit-check puts these together so a sender can see the full cost of a transfer.

**Status:** In development (Oct to Dec 2026). Built for the Chicago Education Advocacy Cooperative (ChiEAC).

## What it will do

- **Transfer cost calculator:** enter a transfer from a receipt and get the total cost (fee + exchange-rate loss + tax) and the yearly cost.
- **Provider comparison:** compare against published World Bank benchmarks.
- **Community Corridor Price Index:** anonymized community submissions, shown by corridor, neighborhood, and quarter. Groups with fewer than 5 entries are hidden.
- **Dashboard:** a public Tableau view of the index.

## Corridors

United States to Mexico, India, and the Philippines.

## Data sources

- [World Bank Remittance Prices Worldwide](https://remittanceprices.worldbank.org) (quarterly provider price data)
- [Frankfurter API](https://frankfurter.dev) (ECB reference exchange rates)
- Federal Reserve H.10 (used to cross-check exchange rates)

## Privacy

No names, addresses, or account numbers are collected. Uploaded files are not stored. Survey responses are anonymized before analysis.

## Repository structure
remitcheck/   calculation engine (Python)
app/          Streamlit web app
etl/          data cleaning and index scripts
data/         datasets and rate cache
docs/         data dictionary, methodology, charter
tests/        automated tests


## Refreshing the benchmark data

1. Download the latest RPW dataset from the World Bank.
2. Load the sheet `Dataset (from Q2 2016)`.
3. Filter to the latest `period` and to the three corridors.

## Data Dictionary

See [docs/data_dictionary.md](docs/data_dictionary.md) for survey fields, CSV columns, computed fields, and data sources.

## License

MIT. See [LICENSE](LICENSE).
