# Singapore buy-timing dashboard

A research dashboard for deciding **when** to buy a car and a home in Singapore, built on the conditional-probability-of-exceedance (CPE) framework of [quant-regime-research](https://github.com/quantarram/quant-regime-research) and in the style of its sister dashboards: public data only, mechanisms registered before any result, thresholds frozen on a formation window, scored forward on a ledger.

It is a research tool, not financial advice.

## Scope

| Phase | What | Status |
|---|---|---|
| 1 | Cars: COE premium, Category A and B, one row per bidding exercise (about every two weeks) | data layer done; first CPE scan found no persistent signal (see below) |
| 2 | Property: executive condominiums, private condominiums (non-landed) and landed | not started |
| 3 | Dashboard: a public panel for any buyer, and a private view for your own budget and timeline (kept out of the repo) | not started |

## Data (public)

- **COE bidding results**: LTA via data.gov.sg (Open Data Licence, no key). 397 exercises, January 2010 to October 2026. `data/coe_results.csv`, refreshed by `pipelines/fetch_coe.py`. Bids received is missing for 109 of 1,985 rows, mostly 2024 to 2026.
- **Private residential price index**: URA via data.gov.sg, quarterly from 1975 (landed and non-landed), non-landed by region from 2004. Not yet fetched.
- **Mortgage rates**: MAS compounded SORA, daily. Not yet fetched.
- **Transactions**: the URA Data Service API needs a free registration and access key. Source for executive condominiums not yet checked.

## First findings (COE)

- Latest premiums (first exercise of October 2026): Category A S$130,001, Category B S$130,100, both near their highs.
- A first scan of 288 registered conditions (quota supply, bid pressure, reversion to the one-year average, momentum; horizons of one to six months; formation to 2017, test from 2018) found nothing that beats the base rate: of 22 conditions admitted on the early years, the mean lift on the test years is 1.09.
- Base rates: the premium rose in 56% of exercises and, over about three months, rose more than 10% in 29% of windows and fell more than 10% in 16%.
- Quota is announced a quarter ahead and is computed from past deregistrations, so the market already knows it.

The research scripts and results are in `notebooks/sg_timing/` of [quant-regime-research](https://github.com/quantarram/quant-regime-research); they will move here as the pipeline is built.

## Layout

```
sgtiming/        data layer (fetching and parsing)
pipelines/       scripts that refresh the data
data/            committed raw public data
private/         your own numbers, ignored by git
```

## Citation and data licence

Cite the repository. The underlying data are published by the Land Transport Authority and other Singapore agencies under the Singapore Open Data Licence.
