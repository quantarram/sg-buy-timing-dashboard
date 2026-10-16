# COE premium: CPE walk-forward (2026-10-16)

Data: monthly series from data.gov.sg, 2002-02 to 2026-09 (296 months), old Category A (cars up to 1,600cc and 97kW) and Category B (above), premium = mean of the two bidding rounds. Code: `coe_cpe_walkforward.py`, `coe_wf_drilldown.py`, `coe_current_state.py`, `coe_summary_figure.py`; figure `coe_walkforward_figure.png`.

## Design
Eight predictor families with the mechanism registered first (quota supply, de-registrations, bid pressure, interest rates, valuation against the one-year mean, valuation against a quota-implied level, the B/A spread, momentum), tau_p of 1 to 12 months, tau_f of 1, 3 and 6 months, X tails of 20% and 10% on each side. For each test year 2010 to 2026 all thresholds and the admission (lift >= 1.5, >= 20 entries, >= 4 episodes, base rate matched on calendar month) use only entries whose outcome had resolved before 1 January of that year. Admitted conditions are scored on that year's entries; pooled lift is against the same-calendar-month base rate over 2010 to 2026. Entries overlap (every month is an entry), so counts of scored months are reported next to episodes.

## Results (horizons of 1, 3, 6 and 12 months; ninth family, the lagged supply cycle, added after the cycle analysis below)
- 848 admitted condition-years (244 distinct conditions), 3,292 scored entries: CPE 0.178 against a base of 0.136, lift 1.31.
- By family (lift, entries): quota-implied level 1.98 (261; see the specification caveat below), quota 1.76 (577), bids 1.70 (42, too few), spread 1.41 (276), momentum 1.29 (389), supply cycle 1.25 (66, only 6 admitted condition-years), de-registrations 1.09, interest rates 0.96. By horizon: one month 0.93, three 1.12, six 1.52, twelve 1.72.
- Rarity: no gradient overall (20% tails 1.34, 10% tails 1.20); inside the quota family the rarer tail is stronger (Category B 2.45 against 1.68).
- The quota effect is one-sided and builds with the horizon. After quota cuts the premium is in its top 20% of moves this often against the base rate: one month 15% against 13%, three months 24% against 16%, six months 34% against 17% (lift 1.98), twelve months 50% against 22% (lift 2.24, 115 entries). Quota increases are not followed by lower premiums (three admitted condition-years).
- It is not stable by year (the quota family scored 3.2 in 2021 and 2.9 in 2012, but 0.3 in 2019 and 0.5 in 2023) and the evidence is roughly 20 to 35 independent windows.
- Quota is announced a quarter ahead and, since 2023, is a four-quarter rolling average of de-registrations, so the market knows it; the result says the premium reacts slowly to it, not that it is a surprise.

## State in September 2026
No admitted condition is in a tail. Category A: premium S$132,450 (prevailing S$128,715), the highest on record; quota change over six months -5.9% (41st percentile); Category B: S$134,000 (prevailing S$131,616), quota up 13% over six months (74th percentile, the side with no evidence). The quota-implied level reads at the 100th percentile for both categories, which is a specification problem (premiums have trended up for reasons that are not quota) and is not used until it is detrended or re-specified.

## Base rates (forward change in the monthly premium)
Category A, last ten years: lower after 3 months 37%, up more than 5% 45%, median +3.1%; after 6 months lower 33%, up more than 5% 55%, median +6.5%. Category B: 3 months lower 40%, up more than 5% 43%; 6 months lower 32%, up more than 5% 50%. These carry the last decade's rising trend.

## Reading
Premium timing is mostly a base-rate problem. The one mechanism with out-of-sample support is a quota cut leading to a higher premium over about six months, and it is uneven across years; no condition is firing now. The dashboard should show the base rates, the quota calendar and the state of the registered predictors, and say plainly that no condition is active.

## A decade-long cycle (`coe_cycle_analysis.py`, `coe_cycle_figure.png`)
- Premium: smoothed troughs in January 2009 and March 2019 (Category A; September 2018 for B), peaks in May 2013 (A) and September 2012 (B); the periodogram of the detrended log premium peaks at 11.6 years for both, and the autocorrelation is about +0.5 at 10 years and +0.8 at 12 years. That is two cycles in 24.7 years, so the period is an estimate, not a finding.
- Mechanism: a COE lasts ten years, so registrations ten years ago are a schedule of expiries. Since 2018 that schedule tracks actual de-registrations closely (correlation of 12-month means 0.96; 0.72 in 2010 to 2017; only 0.33 in the 2000s), and 12-month de-registrations track quota at 0.93.
- Lag: the detrended premium is negatively related to the supply cycle (12-month mean de-registrations) 18 to 24 months earlier: correlation -0.72 (A, 24 months) and -0.67 (B, 18 months), and at 18 months -0.71 in 2002 to 2013 against -0.88 in 2014 to 2026 for A. This is a statement about levels around a trend, not a forecast of tail moves.
- Pipeline: scheduled expiries average 6,770 vehicles a month for the year to August 2026, 7,570 a year ahead and 7,050 two years ahead, against 5,180 actual de-registrations over the last 12 months, so the quota is set to keep rising through 2027 to 2028. At an 18 to 24 month lag that points to easing premium pressure from 2027, but the premium rose to record highs through 2024 to 2026 while de-registrations were already rising from the 2023 low, so demand or the lag is overriding the supply cycle for now.
- As a registered event predictor the lagged supply-cycle change was admitted in only 6 condition-years (lift 1.25), and a simple test of the known-ahead schedule against the next 12 or 24 months of premium change had the wrong sign (+0.15 and +0.17), because the lag is 18 to 24 months. Reading: a real, mechanism-backed cycle that is useful as a description of where the market is in the supply cycle; turning points are not validated as forecasts.
