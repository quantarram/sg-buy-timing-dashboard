# Property: CPE walk-forward and descriptive state (2026-10-16)

Data: URA price and rental indices (2009 Q1 = 100), transactions, launches and sales, supply and vacancy, quarterly to 2026 Q2, from data.gov.sg. Targets: all non-landed, landed, and non-landed by region (core central, rest of central, outside central; regions from 2004). Code: `property_cpe_walkforward.py`, `property_wf_drilldown.py`, `recent_decade_check.py`; `sgtiming/property_predictors.py`, `sgtiming/property_state.py`.

## Design
Nine registered predictor families (price momentum, rent growth, two-year government yield change, supply pipeline change, units transacted change, unsold approved units change, price-to-rent against its five-year mean, vacancy against its five-year mean, new-sale sold/launched), tau_p of 1, 2, 4, 8 quarters, tau_f of 1, 2, 4, 8 quarters, 20% and 10% tails. Statistics other than price, rent and rates enter with a one-quarter lag. Causal walk-forward for test years 2005 to 2026: thresholds and admission (lift >= 1.5, >= 20 entries, >= 4 episodes, base rate matched on the quarter of the year) use only entries resolved before 1 January of the year. A family is called supported on the dashboard only if its lift is at least 1.4 over all test years and since 2017, on at least 100 entries.

## Results
- 1,622 admitted condition-years (534 distinct conditions), 3,072 scored entries: CPE 0.140 against a base of 0.145, lift 0.96; since 2017 the lift is 0.64.
- By family (lift all years, since 2017): momentum 2.13 and 0.69; rent growth 1.20 and 0.57; unsold stock 1.38 and 1.38 (101 entries); sales ratio 1.13 and 1.13 (79); volume 0.81 and 0.83; vacancy 0.76 and 0.17; rates 0.52 and 0.28; pipeline 0.35 and 0.28; price-to-rent 0.31 and 0.31. No family is supported.
- Momentum scored 3.56 up to 2016 (the 2008 to 2010 swings: test-year lifts of 4.4, 6.7, 3.9 and 3.1) and 0.69 since 2017 (zero hits in 2024 to 2026). It worked for the whole non-landed index (4.5) and landed (2.5), not for the core central or outside central series (0.3 and 0.4). Rarer tails did better (5.5 against 1.8). The evidence rests on about 94 scored (target, quarter) cells in 18 years, concentrated in one cycle. Part of any momentum may come from how the index is built; that was not tested.
- Rates, rent growth and vacancy show the same pattern: strong up to 2016 (2.0, 3.5, 2.1), weak since.

## Base rates and drawdowns
- Non-landed index: lower four quarters later 23% of the time since 2004 (worst four-quarter change -30%), against 6% in the last ten years; lower eight quarters later 21% against 0%. Landed: 27% since 2004 (worst -21%) against 14%. The last decade was almost one-way up and flatters the base rate.
- Falls of more than 10% from a peak: non-landed -47% (1981 Q2 to 1986 Q2, 20 quarters down, 20 to recover), -42% (1996 Q2 to 1998 Q4, 10 down, 36 to recover), -26% (2008 Q2 to 2009 Q2, 4 down, 4 to recover), -10% (2013 Q3 to 2017 Q2). Landed -34% (1984 to 1986), -48% (1996 to 1998), -16% (2013 to 2017).

## State at 2026 Q2
All indices are at or within about 1% of their peaks: condo all regions 210.6 (+1.8% year on year), core central 161.5 (+0.5%, 1.2% below its Q3 2025 peak), rest of central 226.2 (+0.6%), outside central 271.1 (+3.9%), landed 258.4 (+7.0%, record). Price-to-rent sits at the 81st (condo), 88th (outside central) and 92nd (landed) percentile of its history, and the 13th for core central. Vacancy 6.4% (37th percentile), unsold approved units 15,057 (4th percentile), new units sold per launched 1.19, transactions +20% year on year. No supported condition is active.

## Reading
For property the tests find no timing signal that survives the latest decade. The dashboard shows risk (drawdown history, base rates over both windows) and the state of the indicators, with WAIT & WATCH as the verdict. Executive condominium prices are not on the public data portal (the URA Data Service API needs a free key), so the EC panel covers activity and supply only.
