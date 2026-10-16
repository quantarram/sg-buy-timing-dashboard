# Singapore buy-timing dashboard

A research dashboard for deciding **when** to buy a car and a home in Singapore, built on the conditional-probability-of-exceedance (CPE) framework of [quant-regime-research](https://github.com/quantarram/quant-regime-research) and in the style of its sister dashboards: public data only, mechanisms registered before any result, thresholds frozen on a formation window, scored forward on a ledger.

It is a general, public research tool with nothing personalised in it, and it is not financial advice.

## Scope

| Phase | What | Status |
|---|---|---|
| 1 | Cars: COE premium, Category A and B (monthly series from 2002) | data layer and causal walk-forward done; one modest supply effect, nothing firing now |
| 2 | Property: executive condominiums, private condominiums (non-landed) and landed | not started |
| 3 | Dashboard: one public panel for any Singapore buyer (general conditions and probabilities, nothing personalised) | not started |

## Data (public)

- **COE results**: LTA via data.gov.sg (Open Data Licence, no key). Per-exercise results from 2010 (`data/coe_results.csv`, `pipelines/fetch_coe.py`; bids received missing for 109 of 1,985 rows) and monthly series from 2002 with bids, quota and premium (`pipelines/fetch_monthly.py`).
- **Vehicle flows and rates**: monthly new registrations and de-registrations by category, and government bond yields and SORA (MAS), all on data.gov.sg.
- **Private residential price index**: URA via data.gov.sg, quarterly from 1975 (landed and non-landed), non-landed by region from 2004. Not yet fetched.
- **Mortgage rates**: MAS compounded SORA, daily. Not yet fetched.
- **Transactions**: the URA Data Service API needs a free registration and access key. Source for executive condominiums not yet checked.

## First findings (COE)

Monthly series from 2002 (296 months), old Category A and B, eight registered predictor families, a causal walk-forward from 2010 (details and caveats in `research/RESULTS.md`).

- Latest (September 2026, monthly mean of the two rounds): Category A S$132,450, the highest on record; Category B S$134,000.
- Overall the walk-forward lift is modest (1.21). Supply-side conditions did best: after a quota cut the premium was in its top 20% of six-month moves 34% of the time against a 17% base. Interest rates, de-registrations and momentum added nothing, and the effect is uneven from year to year.
- No admitted condition is firing now. The dashboard will show base rates, the quota calendar and the state of each predictor, and say so when nothing is active.
- Base rates over the last ten years: after three months the Category A premium was higher 63% of the time and rose more than 5% in 45% of windows; after six months the median change was +6.5%. These carry a decade of rising premiums.

## Layout

```
sgtiming/        data layer (fetching, parsing, monthly panel)
research/        CPE walk-forward, drill-downs, results
pipelines/       scripts that refresh the data
data/            committed raw public data
```

## Citation and data licence

Cite the repository. The underlying data are published by the Land Transport Authority and other Singapore agencies under the Singapore Open Data Licence.
