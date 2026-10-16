# COE premium: CPE walk-forward (2026-10-16)

Data: monthly series from data.gov.sg, 2002-02 to 2026-09 (296 months), old Category A (cars up to 1,600cc and 97kW) and Category B (above), premium = mean of the two bidding rounds. Code: `coe_cpe_walkforward.py`, `coe_wf_drilldown.py`, `coe_current_state.py`, `coe_summary_figure.py`; figure `coe_walkforward_figure.png`.

## Design
Eight predictor families with the mechanism registered first (quota supply, de-registrations, bid pressure, interest rates, valuation against the one-year mean, valuation against a quota-implied level, the B/A spread, momentum), tau_p of 1 to 12 months, tau_f of 1, 3 and 6 months, X tails of 20% and 10% on each side. For each test year 2010 to 2026 all thresholds and the admission (lift >= 1.5, >= 20 entries, >= 4 episodes, base rate matched on calendar month) use only entries whose outcome had resolved before 1 January of that year. Admitted conditions are scored on that year's entries; pooled lift is against the same-calendar-month base rate over 2010 to 2026. Entries overlap (every month is an entry), so counts of scored months are reported next to episodes.

## Results
- 715 admitted condition-years (198 distinct conditions), 2,714 scored entries: CPE 0.160 against a base of 0.132, lift 1.21.
- By family (lift, entries): quota 1.59 (462), bids 1.70 (42, too few), quota-implied level 1.49 (213), spread 1.41 (255); momentum 1.07, de-registrations 1.04, interest rates 1.00. By horizon: one month 0.93, three months 1.12, six months 1.52.
- Rarity: no gradient overall (20% tails 1.26, 10% tails 1.06); inside the quota family the rarer tail is stronger (1.83 against 1.47).
- The quota effect is one-sided. After quota cuts the premium is in its top 20% of six-month moves 34% of the time against 17% (lift 1.98, 153 entries; three months 1.51, one month 1.15). Quota increases are not followed by lower premiums (three admitted condition-years). The effect builds over about six months.
- It is not stable: the quota family scored 3.2 in 2021 and 2.9 in 2012 but 0.3 in 2019 and 0.5 in 2023. The 105 scored (category, month) cells in the quota family cover 13 years and amount to roughly 20 to 35 independent three-to-six-month windows.
- Quota is announced a quarter ahead and, since 2023, is a four-quarter rolling average of de-registrations, so the market knows it; the result says the premium reacts slowly to it, not that it is a surprise.

## State in September 2026
No admitted condition is in a tail. Category A: premium S$132,450 (prevailing S$128,715), the highest on record; quota change over six months -5.9% (41st percentile); Category B: S$134,000 (prevailing S$131,616), quota up 13% over six months (74th percentile, the side with no evidence). The quota-implied level reads at the 100th percentile for both categories, which is a specification problem (premiums have trended up for reasons that are not quota) and is not used until it is detrended or re-specified.

## Base rates (forward change in the monthly premium)
Category A, last ten years: lower after 3 months 37%, up more than 5% 45%, median +3.1%; after 6 months lower 33%, up more than 5% 55%, median +6.5%. Category B: 3 months lower 40%, up more than 5% 43%; 6 months lower 32%, up more than 5% 50%. These carry the last decade's rising trend.

## Reading
Premium timing is mostly a base-rate problem. The one mechanism with out-of-sample support is a quota cut leading to a higher premium over about six months, and it is uneven across years; no condition is firing now. The dashboard should show the base rates, the quota calendar and the state of the registered predictors, and say plainly that no condition is active.
