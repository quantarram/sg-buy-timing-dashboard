# Singapore buy-timing dashboard

A research dashboard for deciding **when** to buy a car and a home in Singapore, built on the conditional-probability-of-exceedance (CPE) framework of [quant-regime-research](https://github.com/quantarram/quant-regime-research) and in the style of its sister dashboards: public data only, mechanisms registered before any result, thresholds frozen on a formation window, scored forward on a ledger.

**Live dashboard: https://quantarram.github.io/sg-buy-timing-dashboard/** (rebuilt daily; the figures change when new data are published).

It is a general, public research tool with nothing personalised in it, and it is not financial advice.

**Paper:** Ramanathan S, A. (2026). *The Ten-Year Echo in Singapore's COE Premium, and Why Housing Timing Signals Fail Out of Sample.* Zenodo, [doi:10.5281/zenodo.23418466](https://doi.org/10.5281/zenodo.23418466) (Paper 18 of the CPE research series). Write-up: [Substack](https://arunramanathans.substack.com/p/the-ten-year-echo-in-singapores-coe).

**Author:** Arun Ramanathan, PhD (Independent Researcher, Singapore) · [LinkedIn](https://www.linkedin.com/in/arun-rs) · [Substack](https://arunramanathans.substack.com) · [CPE research program](https://github.com/quantarram/quant-regime-research)

## Scope

| Phase | What | Status |
|---|---|---|
| 1 | Cars: COE premium, Category A and B (monthly series from 2002) | data layer and causal walk-forward done; one modest supply effect, nothing firing now |
| 2 | Property: executive condominiums, private condominiums (non-landed) and landed | data layer and causal walk-forward done: no timing signal survives the latest decade; EC prices from URA transactions |
| 3 | Dashboard: one public panel for any Singapore buyer (general conditions and probabilities, nothing personalised), a lookup for any HDB block and a forward ledger that scores its own forecasts | live; rebuilt daily |

## Data (public)

- **COE results**: LTA via data.gov.sg (Open Data Licence, no key). Per-exercise results from 2010 (`data/coe_results.csv`, `pipelines/fetch_coe.py`; bids received missing for 109 of 1,985 rows) and monthly series from 2002 with bids, quota and premium (`pipelines/fetch_monthly.py`).
- **Vehicle flows and rates**: monthly new registrations and de-registrations by category, and government bond yields and SORA (MAS), all on data.gov.sg.
- **Property (URA and related, quarterly, to 2026 Q2)**, fetched by `pipelines/fetch_property.py` into `data/property/` and parsed by `sgtiming/property_panel.py`:
  - prices: private residential price index (all, landed, non-landed; from 1975) and non-landed by region (core central, rest of central, outside central; from 2004);
  - rents: private residential rental index (from 1990; non-landed by region from 2004);
  - activity: units transacted (new sale, resale, sub sale; whole island from 1999 and by region from 2004), uncompleted units launched and sold by region, completed units sold;
  - supply: pipeline by status (landed and non-landed, from 1993), available and vacant stock (from 1988), unsold approved units (from 2006);
  - executive condominiums: launches, new and resale sales, sale position, available, vacant and pipeline (from 2008 to 2010); **no EC price series is on data.gov.sg**, so EC and condo prices per square foot come from the URA Data Service API (free access key; five years of single-unit transactions, updated Tuesdays and Fridays; only monthly aggregates are committed).
- **HDB resale transactions** (HDB via data.gov.sg): every registered resale since March 2012 (331,529 transactions, 9,826 blocks). `pipelines/build_hdb.py` builds a search index and one compact file per town in `docs/hdb/`, which the page uses for the block lookup; raw transactions are not committed.
- **Mortgage benchmark**: compounded SORA and government yields (monthly), already in the monthly series above.

**Preprint:** [Zenodo](https://zenodo.org/records/23418466) (also `paper/singapore_timing_paper_draft.pdf`): the ten-year echo in the COE premium, and why housing timing signals fail out of sample. Rebuilt from the data by `paper/build.sh`; every number is recomputed by `paper/paper_numbers.py`.

**Track record:** the page keeps a forward ledger in `data/ledger/` (base-rate forecasts logged each month or quarter, and any active supported condition, scored as outcomes arrive) and replays the base rates causally over the past; both are updated by the daily workflow (`pipelines/update_ledger.py`).

**Worked example:** [selling a five-room flat on floors 10 to 15 at BLK 184 Jelebu Rd](https://quantarram.github.io/sg-buy-timing-dashboard/example-184-jelebu.html), a dated snapshot built by `pipelines/build_example.py` from public HDB data; the HDB index walk-forward is `research/hdb_rpi_cpe_walkforward.py`.

## First findings (COE)

Monthly series from 2002 (296 months), old Category A and B, eight registered predictor families, a causal walk-forward from 2010 (details and caveats in `research/RESULTS.md`).

- Latest (September 2026, monthly mean of the two rounds): Category A S$132,450, the highest on record; Category B S$134,000.
- Overall the walk-forward lift is modest (1.31 over 848 condition-years). Two families meet the support rule: quota change (lift 1.76) and the Category B/A spread (1.41). After a quota cut the premium was in its top 20% of moves 49% of the time twelve months later, against 24% normally; it held across all 27 tail-threshold combinations and in both 2010 to 2016 and 2017 to 2021, but it is **not detected from 2022** (lift 1.3 on 17 entries; the quota formula changed in August 2022 and February 2023). Interest rates and short-run de-registrations added nothing.
- There is a decade-long cycle (premium troughs in 2009 and 2019, peaks around 2013): it follows the ten-year COE life, which drives de-registrations and so quota, with the premium lagging the supply cycle by 18 to 24 months. Scheduled expiries point to rising quota through 2027 to 2028. Only two cycles, so turning points are not validated as forecasts.
- No admitted condition is firing now. The dashboard will show base rates, the quota calendar and the state of each predictor, and say so when nothing is active.
- Base rates over the last ten years: after three months the Category A premium was higher 63% of the time and rose more than 5% in 45% of windows; after six months the median change was +6.5%. These carry a decade of rising premiums.

## First findings (property)

- Quarterly URA series to 2026 Q2; all price indices are at or near their peaks (landed +7.0% year on year, condo +1.8%).
- A causal walk-forward over nine registered predictor families (1,622 condition-years) finds nothing that beats the base rate in the latest decade (lift 0.96 overall, 0.64 since 2017). Price momentum scored 3.6 up to 2016 (the 2008 to 2010 swings) and 0.7 since. The HDB Resale Price Index scores 0.82 overall and 0.28 since 2017.
- The last decade was almost one-way up, so the long view carries the risk: non-landed prices fell 47% (1981 to 1986), 42% (1996 to 1998), 26% (2008 to 2009) and 10% (2013 to 2017). Details in `research/PROPERTY_RESULTS.md`.

## Layout

```
sgtiming/        data layer (fetching, parsing, monthly COE panel, quarterly property panel)
research/        CPE walk-forward, drill-downs, results
pipelines/       scripts that refresh the data
data/            committed raw public data
```

## Citation and data licence

If you use this work, please cite the paper (GitHub's "Cite this repository" button, from `CITATION.cff`, gives the same):

```
RAMANATHAN S, A. (2026). The Ten-Year Echo in Singapore's COE Premium, and Why
Housing Timing Signals Fail Out of Sample. Zenodo.
https://doi.org/10.5281/zenodo.23418466
```

```bibtex
@misc{ramanathan2026tenyearecho,
  author    = {Ramanathan S, Arun},
  title     = {The Ten-Year Echo in Singapore's COE Premium, and Why Housing Timing Signals Fail Out of Sample},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.23418466},
  url       = {https://doi.org/10.5281/zenodo.23418466}
}
```

The underlying data are published by the Land Transport Authority, the Housing and Development Board, the Urban Redevelopment Authority, the Monetary Authority of Singapore and the Department of Statistics under the Singapore Open Data Licence (URA Data Service transactions are used under its terms; only monthly aggregates are committed). This is research, not financial advice.
