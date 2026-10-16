# Singapore buy-timing dashboard

A research dashboard for deciding **when** to buy a car and a home in Singapore, built on the conditional-probability-of-exceedance (CPE) framework of [quant-regime-research](https://github.com/quantarram/quant-regime-research) and in the style of its sister dashboards: public data only, mechanisms registered before any result, thresholds frozen on a formation window, scored forward on a ledger.

**Live dashboard: https://quantarram.github.io/sg-buy-timing-dashboard/** (rebuilt daily; the figures change when new data are published).

It is a general, public research tool with nothing personalised in it, and it is not financial advice.

## Scope

| Phase | What | Status |
|---|---|---|
| 1 | Cars: COE premium, Category A and B (monthly series from 2002) | data layer and causal walk-forward done; one modest supply effect, nothing firing now |
| 2 | Property: executive condominiums, private condominiums (non-landed) and landed | data layer and causal walk-forward done: no timing signal survives the latest decade; EC prices need a URA key |
| 3 | Dashboard: one public panel for any Singapore buyer (general conditions and probabilities, nothing personalised) | not started |

## Data (public)

- **COE results**: LTA via data.gov.sg (Open Data Licence, no key). Per-exercise results from 2010 (`data/coe_results.csv`, `pipelines/fetch_coe.py`; bids received missing for 109 of 1,985 rows) and monthly series from 2002 with bids, quota and premium (`pipelines/fetch_monthly.py`).
- **Vehicle flows and rates**: monthly new registrations and de-registrations by category, and government bond yields and SORA (MAS), all on data.gov.sg.
- **Property (URA and related, quarterly, to 2026 Q2)**, fetched by `pipelines/fetch_property.py` into `data/property/` and parsed by `sgtiming/property_panel.py`:
  - prices: private residential price index (all, landed, non-landed; from 1975) and non-landed by region (core central, rest of central, outside central; from 2004);
  - rents: private residential rental index (from 1990; non-landed by region from 2004);
  - activity: units transacted (new sale, resale, sub sale; whole island from 1999 and by region from 2004), uncompleted units launched and sold by region, completed units sold;
  - supply: pipeline by status (landed and non-landed, from 1993), available and vacant stock (from 1988), unsold approved units (from 2006);
  - executive condominiums: launches, new and resale sales, sale position, available, vacant and pipeline (from 2008 to 2010); **no EC price series is on data.gov.sg**, so EC prices need the URA Data Service API, which needs a free access key.
- **Mortgage benchmark**: compounded SORA and government yields (monthly), already in the monthly series above.

## First findings (COE)

Monthly series from 2002 (296 months), old Category A and B, eight registered predictor families, a causal walk-forward from 2010 (details and caveats in `research/RESULTS.md`).

- Latest (September 2026, monthly mean of the two rounds): Category A S$132,450, the highest on record; Category B S$134,000.
- Overall the walk-forward lift is modest (1.31). Supply-side conditions did best: after a quota cut the premium was in its top 20% of twelve-month moves 50% of the time against a 22% base. Interest rates and de-registrations added nothing, and the effect is uneven from year to year.
- There is a decade-long cycle (premium troughs in 2009 and 2019, peaks around 2013): it follows the ten-year COE life, which drives de-registrations and so quota, with the premium lagging the supply cycle by 18 to 24 months. Scheduled expiries point to rising quota through 2027 to 2028. Only two cycles, so turning points are not validated as forecasts.
- No admitted condition is firing now. The dashboard will show base rates, the quota calendar and the state of each predictor, and say so when nothing is active.
- Base rates over the last ten years: after three months the Category A premium was higher 63% of the time and rose more than 5% in 45% of windows; after six months the median change was +6.5%. These carry a decade of rising premiums.

## First findings (property)

- Quarterly URA series to 2026 Q2; all price indices are at or near their peaks (landed +7.0% year on year, condo +1.8%).
- A causal walk-forward over nine registered predictor families finds nothing that beats the base rate in the latest decade (lift 0.64 since 2017). Price momentum scored 3.6 up to 2016 (the 2008 to 2010 swings) and 0.7 since.
- The last decade was almost one-way up, so the long view carries the risk: non-landed prices fell 47% (1981 to 1986), 42% (1996 to 1998), 26% (2008 to 2009) and 10% (2013 to 2017). Details in `research/PROPERTY_RESULTS.md`.

## Layout

```
sgtiming/        data layer (fetching, parsing, monthly COE panel, quarterly property panel)
research/        CPE walk-forward, drill-downs, results
pipelines/       scripts that refresh the data
data/            committed raw public data
```

## Citation and data licence

Cite the repository. The underlying data are published by the Land Transport Authority and other Singapore agencies under the Singapore Open Data Licence.
