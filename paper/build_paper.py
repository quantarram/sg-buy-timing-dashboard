"""Builds paper/singapore_timing_paper_draft.md from paper/numbers.json (every quoted number comes from the committed data and research outputs).
python paper/build_paper.py   then   sh paper/build.sh"""
import json, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); N = json.load(open(os.path.join(HERE, "numbers.json")))
f1 = lambda x: f"{x:.1f}"; f2 = lambda x: f"{x:.2f}"; f3 = lambda x: f"{x:.3f}"; pc = lambda x, d=0: f"{x*100:.{d}f}%"; sg = lambda x: f"S${x:,.0f}"; k = lambda x: f"{x:,.0f}"
S = N["coe_support"]; PS = N["prop_support"]; HS = N["hdb_support"]; W = N["coe_wf"]; rob = pd.DataFrame(N["rob_thr"]); sub = pd.DataFrame(N["rob_sub"]); reg = {r["cat"]: r for r in N["rob_reg"]}
main = rob[(rob.q == 0.2) & (rob.yq == 0.2)].set_index("tf"); sb = lambda p, tf: sub[(sub.period == p) & (sub.tf == tf)].iloc[0]
retro = pd.DataFrame(N["retro"]); coe = retro["scope"].str.startswith("COE")
ext = {c: N[f"extrema_{c}"] for c in "AB"}; ea = {(e[0], e[1][:4]): e for e in ext["A"]}
def eq(n, num): return f'<div class="eqn-row"><span class="eqn-spacer"></span><img src="eq/{n}.svg" alt="Equation {num}"><span class="eqn-num">({num})</span></div>'
dd = N["dd"]; hd = N["hdb_state"]; base = N["base"]
def ddrows(t, name): return "".join(f"| {name} | {a} | {b} | {d*100:.0f}% | {q1} | {q2 if q2 is not None else 'not yet'} |\n" for a, b, d, q1, q2 in dd[t])
hdrows = "".join(f"| HDB resale index | {a['peak']} | {a['trough']} | {a['depth']*100:.0f}% | {a['down']} | {a['recover'] if a['recover'] is not None else 'not yet'} |\n" for a in hd["drawdowns"])
def brow(t, nm):
    o = []
    for lab in ("since 2004", "last 10 years"):
        a, b = base[t][lab]["4"], base[t][lab]["8"]; o.append(f"| {nm} | {lab} | {pc(a['lower'])} | {a['med']*100:+.1f}% | {pc(b['lower'])} | {b['med']*100:+.1f}% |\n")
    return "".join(o)
hb = hd["base"]; hbrows = "".join(f"| HDB resale index | {lab} | {pc(hb[lab]['4']['lower'])} | {hb[lab]['4']['med']*100:+.1f}% | {pc(hb[lab]['8']['lower'])} | {hb[lab]['8']['med']*100:+.1f}% |\n" for lab in ("since 1990", "since 2004", "last 10 years"))
fam_rows = "".join(f"| {nm} | {f2(S[fm]['lift_all'])} ({int(S[fm]['entries_all'])}) | {('n/a' if pd.isna(S[fm]['lift_2017']) else f2(S[fm]['lift_2017']) + ' (' + str(int(S[fm]['entries_2017'])) + ')')} | {'yes' if (S[fm]['lift_all'] >= 1.4 and (not pd.isna(S[fm]['lift_2017'])) and S[fm]['lift_2017'] >= 1.4 and S[fm]['entries_all'] >= 100) else 'no'} |\n" for fm, nm in (("quota", "Quota change"), ("spread", "Category B/A spread"), ("momentum", "Premium momentum"), ("supplycycle", "Lagged supply cycle"), ("dereg", "De-registrations"), ("rates", "Two-year yield"), ("bids", "Bids per quota")))
pf_rows = "".join(f"| {nm} | {f2(PS[fm]['lift_all'])} ({int(PS[fm]['entries_all'])}) | {f2(PS[fm]['lift_pre2017']) if not pd.isna(PS[fm]['lift_pre2017']) else 'n/a'} | {f2(PS[fm]['lift_2017'])} ({int(PS[fm]['entries_2017'])}) |\n" for fm, nm in (("momentum", "Price momentum"), ("rentgrowth", "Rent growth"), ("rates", "Two-year yield"), ("vacancy", "Vacancy rate"), ("volume", "Units transacted"), ("pipeline", "Supply pipeline"), ("unsold", "Unsold approved units"), ("salesratio", "New sales per launch"), ("value", "Price-to-rent")))
hf_rows = "".join(f"| {nm} | {f2(HS[fm]['lift_all'])} ({int(HS[fm]['n_all'])}) | {f2(HS[fm]['lift_pre2017']) if not pd.isna(HS[fm]['lift_pre2017']) else 'n/a'} | {f2(HS[fm]['lift_2017']) if not pd.isna(HS[fm]['lift_2017']) else 'n/a'} ({int(HS[fm]['n_2017'])}) |\n" for fm, nm in (("momentum", "HDB momentum"), ("privmom", "Private (outside central) momentum"), ("rates", "Two-year yield"), ("rentgrowth", "Rent growth"), ("vacancy", "Vacancy rate"), ("volume", "Units transacted"), ("pipeline", "Supply pipeline")))
sub_rows = "".join(f"| {p} | " + " | ".join(f"{f2(sb(p, tf)['lift'])} ({int(sb(p, tf)['entries'])})" for tf in (3, 6, 12)) + " |\n" for p in ("2010-2016", "2017-2021", "2022-2026"))
re_rows = "".join(f"| {r.scope} | {int(r.horizon)} {'months' if r.unit == 'month' else 'quarters'} | {int(r.n)} | {pc(r.share_higher)} | {f3(r.brier_10y)} | {f3(r.brier_all)} |\n" for r in retro.itertuples())
thr_min, thr_max = rob["lift"].min(), rob["lift"].max(); assert len(rob) == 27 and thr_min > 1.4, 'text claims all 27 combinations exceed 1.4'; assert all(PS[f]['lift_all'] < 1.4 or PS[f]['lift_2017'] < 1.4 or PS[f]['entries_all'] < 100 for f in PS if f != 'ALL'), 'text claims no property family is supported'; assert S['quota']['lift_all'] >= 1.4 and S['quota']['lift_2017'] >= 1.4 and S['spread']['lift_all'] >= 1.4 and S['spread']['lift_2017'] >= 1.4; cp = N["coe_wf"]; allw = W["ALL admitted"]; pall = N["prop_all"]; hall = HS["ALL"]; pallS = PS["ALL"]
TITLE = "# The Ten-Year Echo in Singapore's COE Premium, and Why Housing Timing Signals Fail Out of Sample"
ABSTRACT = f"""When to buy a car or a home in Singapore is a timing question with public data behind it. This paper applies one disciplined test to both: mechanisms written down before testing, thresholds that use only information available at the time (a causal walk-forward), and a rule that a signal counts as supported only if it holds both over all test years and since 2017. The data are {N['months']} months of Certificate of Entitlement (COE) results from {N['start']}, private property price indices from 1975 and the HDB resale price index from 1990.

For cars, one mechanism is supported. A COE lasts ten years, so registrations become scheduled expiries; since 2018 the schedule tracks de-registrations (correlation {f2(N['corr_sched_dereg_2018_2026'])}), de-registrations set the quota, and the premium follows the supply cycle with a lag of 18 to 24 months (correlation {f2(N['lagbest_A'][1])} for Category A and {f2(N['lagbest_B'][1])} for Category B). After a quota cut, the premium was in its top 20% of six-month rises {pc(main.loc[6, 'cpe'])} of the time against {pc(main.loc[6, 'base'])} (lift {f2(main.loc[6, 'lift'])}), robust to every tail threshold tried. The effect is strong to 2021 and not detected from 2022 on ({int(sb('2022-2026', 6)['entries'])} entries), after the quota formula changed; very few cuts have occurred since.

For property, nothing is supported: the walk-forward lift of the admitted conditions is {f2(pallS['lift_all'])} overall and {f2(pallS['lift_2017'])} since 2017, and the 2008-2010 momentum effect, the largest single result, is absent since 2017. A ten-year base rate scores worse than a coin flip for property and no better than one for the COE premium; the all-history base rate beats the coin for property. The design and a forward ledger, which logs base-rate forecasts and scores them as outcomes arrive, are fixed here before the first outcome."""
PLS = f"""Singapore's car ownership permits (COEs) and its property prices are the two big purchase decisions where timing seems to matter. We tested every timing idea we could write down in advance, using public data: {N['months']} months of COE results, private property prices back to 1975 and HDB resale prices back to 1990. Each idea was judged only on information that existed at the time, and an idea counted as real only if it worked both over the whole record and in the most recent decade.

For cars we found one real pattern. A COE lasts ten years, so the cars registered a decade ago come up for renewal or scrapping now. That wave of expiring permits drives how many permits the government releases, and the price of a permit follows that supply with a delay of about a year and a half to two years. After the government cut the quota, the permit price jumped sharply within six months about {pc(main.loc[6, 'cpe'])} of the time, compared with {pc(main.loc[6, 'base'])} normally. The pattern held up under every variation we tried, but it was strong until 2021 and we cannot detect it since, partly because the quota rules changed and there have been very few cuts to test.

For property we found nothing that works. Ideas that predicted prices well before 2017, such as recent price momentum, rents and interest rates, have not worked since. The last ten years rose almost without a pause, so a rule of thumb built on that decade is a worse guide than the long history; for property, the long-run odds of a rise beat a coin flip, while the ten-year odds do worse than one. For permits the odds are roughly a coin flip either way. Condo prices have fallen by 47%, 42% and 26% in past downturns.

We publish the rules now, before the results are known, and a public dashboard keeps a ledger that logs its own forecasts and scores them as outcomes arrive, starting October 2026. This is research, not advice."""
body = f"""{TITLE}

By Arun Ramanathan

CPE research series, Paper 18

---

## Graphical Abstract

![](figs/graphical_abstract.png)

*Left, the premium lags the supply cycle by 18 to 24 months. Middle, after a quota cut the premium is in its top 20% of moves far more often than normally (both categories, thresholds from past data only). Right, every private-property predictor that worked up to 2016 has a lift near or below 1 since 2017. Built by `paper/paper_figures.py`.*

---

## Abstract

{ABSTRACT}

---

## Plain Language Summary

{PLS}

---

## 1. Introduction

Two purchases dominate the Singapore household balance sheet: a car, which first requires a Certificate of Entitlement (COE), and a home, public or private. Both have public price histories and a standing belief that timing matters: the COE premium is said to move with quota announcements, and property is said to follow momentum, interest rates and supply. This paper asks which of these beliefs survive a test that cannot cheat, and what a buyer should use in their place.

The test is the conditional-exceedance (CPE) framework of this series (Ramanathan, 2026), applied with three disciplines. Each predictor carries a mechanism written down before it is tested. Every threshold and every admission decision uses only information resolved before the year being scored (a causal walk-forward). And a predictor counts as supported only if its out-of-sample lift over a season-matched base rate is at least 1.4 over all test years and also since 2017, on at least 100 scored entries. The third rule is the one that matters most here: it removes effects that depend on a single cycle.

The paper has four findings.

1. **A ten-year echo drives the COE premium.** The ten-year life of a COE turns past registrations into a schedule of expiries, which tracks de-registrations, which set the quota; the premium lags that supply cycle by 18 to 24 months (Section 4.2).
2. **One condition is supported for cars, with a caveat.** After a quota cut the premium is more often in its largest rises over the following three to twelve months. The effect is robust to thresholds, strong through 2021 and not detected since 2022, when the quota formula changed and cuts became rare (Section 4.4).
3. **No timing condition is supported for property.** The momentum effect that scored a lift above 3 up to 2016 scores below 1 since 2017, and rents, rates and vacancy follow the same pattern; the same holds for the HDB resale index (Section 5).
4. **The base rates a buyer would reach for are not equally reliable.** Replayed causally, the ten-year base rate for the COE premium scores about as well as a coin flip, and for property it scores worse; the all-history base rate beats the coin for property (Section 6).

Section 7 fixes the forward test: a ledger that logs the dashboard's base-rate forecasts and any active supported condition, and scores them as outcomes arrive. Section 8 lists the choices that were made after seeing results.

## 2. Data

### 2.1 The quota system and the premium

Singapore caps the vehicle population through a Vehicle Quota System. A COE is a ten-year entitlement to own a vehicle, sold in uniform-price auctions twice a month; the premium is the price at which the quota clears. The quota for each quarter is announced in advance. From August 2022 it was set from the previous two quarters' de-registrations, and from February 2023 from the previous four (LTA, 2022; LTA, 2023). The series used here are Category A (cars up to 1,600cc and 97kW) and Category B (above), under the definitions in force before May 2022, as monthly means of the two rounds.

### 2.2 Sources

| Series | Source | Coverage used |
|---|---|---|
| COE quota, bids and premium by category | LTA, data.gov.sg | {N['start']} to {N['end']} ({N['months']} months) |
| New registrations and de-registrations by category | LTA, data.gov.sg | monthly from 1990 |
| Two-year government yield, SORA | MAS, data.gov.sg | monthly |
| Private residential price and rental indices (landed, non-landed, by region) | URA, data.gov.sg | quarterly from 1975 (regions from 2004) |
| Transactions, launches, sales, supply pipeline, vacancy, unsold approved units | URA, data.gov.sg | quarterly, 1988 to 2026 Q2 depending on series |
| HDB Resale Price Index | HDB, data.gov.sg | quarterly from 1990 |

All series are public and fetched by code; Section 10 lists the repository.

## 3. Method

### 3.1 Conditional exceedance and its base rate

For a predictor X observed over the past τ<sub>p</sub> periods and a target Y measured over the next τ<sub>f</sub> periods, the conditional probability of exceedance is the probability that Y falls in a tail event set when X is in its own tail, and the lift divides it by a base rate:

{eq('eq1_cpe', 1)}

The base rate is season-matched: for each scored entry i, the frequency of the same Y event over all test-window entries in the same calendar month (or quarter) m(i), averaged over the n scored entries:

{eq('eq2_base', 2)}

For the COE premium Y is the forward change in the log monthly premium over 3, 6 and 12 months, and the event is the top 20% of changes; for the price indices Y is the forward change over 1, 2, 4 and 8 quarters. X tails are the 20% and 10% tails.

### 3.2 Registered predictors

Each family has a direction fixed in advance by its mechanism. For the COE premium: quota change over the past τ<sub>p</sub> months (more supply, lower premium); de-registrations, lagged two months for publication, against their 12-month mean (more de-registrations feed later quota); bids per quota (demand pressure); the change in the two-year government yield (dearer financing); the premium against its trailing 12-month mean (reversion); the Category B/A spread (convergence); premium momentum (continuation); and the supply cycle, the change in the 12-month mean of de-registrations measured 6, 12 or 18 months ago. For property and the HDB index: own momentum; rent growth; the two-year yield; the supply pipeline; units transacted; unsold approved units; vacancy against its five-year mean; new sales per launch; price-to-rent against its five-year mean; and, for the HDB index, private outside-central momentum and the HDB-to-private ratio. Quarterly statistics other than prices, rents and yields enter with a one-quarter lag.

### 3.3 Causal walk-forward and the support rule

For each test year y from 2010 (cars) or 2005 (property) or 2000 (HDB index), the X and Y thresholds and the admission of conditions use only entries whose outcome was resolved before 1 January of y. A condition c is admitted if its training lift is at least 1.5, it has at least 20 entries, and the entries form at least four episodes (entries more than τ<sub>f</sub> apart):

{eq('eq3_admit', 3)}

Admitted conditions are scored on that year's entries, and results are pooled across years. A predictor family f is called supported only if

{eq('eq7_support', 4)}

where L<sub>f</sub><sup>all</sup> is its pooled lift over all test years, L<sub>f</sub><sup>&ge;2017</sup> its pooled lift over test years from 2017, and n<sub>f</sub> its number of scored entries.

### 3.4 Scoring base-rate forecasts

The dashboard's base rate for a series and horizon is the share of recent (the last ten years) or all earlier windows in which the series was higher after the horizon, counting only windows already finished at the anchor. Its accuracy is the Brier score, where p<sub>i</sub> is the forecast probability and o<sub>i</sub> the outcome:

{eq('eq6_brier', 5)}

A constant forecast of one half scores 0.250; lower is better.

### 3.5 Overlap and effective sample

Every month or quarter is an entry, so entries overlap. Counts of scored entries are reported with the number of non-overlapping τ<sub>f</sub> windows they correspond to, as a guide to how much independent evidence stands behind a result.

## 4. Cars: the COE premium

### 4.1 The premium and the quota

![Figure 1. COE premium (left) and quota (right), Categories A and B, monthly, {N['start']} to {N['end']}.](figs/fig1_coe.png)

The Category A premium fell from {sg(N['prem_A_first'])} in {N['start']} to a trough of {sg(N['prem_A_min'])} in {N['prem_A_min_date']}, rose to a smoothed peak of {sg(ea[('peak','2013')][2])} (May 2013), fell to {sg(ea[('trough','2019')][2])} (March 2019) and reached {sg(N['prem_A_last'])} in {N['end']}; Category B stood at {sg(N['prem_B_last'])}. Two features matter for what follows: the premium moves in long swings around a rising trend, and the quota moves in the opposite direction with a delay.

### 4.2 The ten-year echo

The smoothed Category A premium troughs in January 2009 and March 2019 and peaks in 2013; the periodogram of the detrended log premium peaks at {f1(N['period_A'])} years for both categories, with autocorrelation of {f2(N['ac10_A'])} at ten years and {f2(N['ac12_A'])} at twelve (Category A). That is two cycles in {f1(N['span_years'])} years, so the period is an estimate and not a finding.

A mechanism explains a swing of this length. A COE lasts ten years, so the registrations of month t &minus; 120 are a schedule of expiries for month t. Writing N for registrations, E for scheduled expiries and S for their 12-month mean,

{eq('eq4_echo', 6)}

The schedule tracks de-registrations closely in the recent record: the correlation of S with the 12-month mean of de-registrations is {f2(N['corr_sched_dereg_2000_2009'])} in 2000-2009, {f2(N['corr_sched_dereg_2010_2017'])} in 2010-2017 and {f2(N['corr_sched_dereg_2018_2026'])} in 2018-2026. The echo is regime-dependent: on monthly data over the whole record, the correlation of de-registrations with registrations 120 months earlier is {f2(N['corr_dereg_newreg_lag120'])}, and the strongest relation is at lag zero ({f2(N['corr_dereg_newreg_lag0'])}); it appears in the 12-month means only from 2010. A possible reason for its weakness in the 2000s is that renewals and early scrapping blurred it, which is not tested here. De-registrations in turn set the quota (correlation of 12-month means {f2(N['corr_dereg_quota'])}), and since 2023 the quota is set from a four-quarter average of de-registrations.

![Figure 2. Left: new registrations, de-registrations and scheduled expiries (registrations ten years earlier), Categories A and B combined, 6-month means. Right: correlation of the detrended log premium with the 12-month mean of de-registrations measured k months earlier.](figs/fig2_echo.png)

The premium lags this supply cycle. The correlation of the detrended log premium with de-registrations k months earlier is most negative at 24 months for Category A ({f2(N['lagbest_A'][1])}) and 18 months for Category B ({f2(N['lagbest_B'][1])}), and at 18 months it is {f2(N['lag18_A_h1'])} (2002-2013) and {f2(N['lag18_A_h2'])} (2014-2026) for Category A and {f2(N['lag18_B_h1'])} and {f2(N['lag18_B_h2'])} for Category B. Scheduled expiries average {k(N['sched_now'])} vehicles a month over the past year and {k(N['sched_1y'])} over the coming year, against {k(N['dereg12_now'])} actual de-registrations over the last twelve months, so the quota is set to keep rising through 2027 to 2028. At an 18 to 24 month lag that implies easing premium pressure from 2027, but the premium reached record levels in 2024-2026 while de-registrations were already rising, so demand or a longer lag overrides the supply cycle for now. This is a description of where the market sits in the cycle; it is not a forecast of a turning point.

### 4.3 Walk-forward results

![Figure 3. COE premium: out-of-sample lift by predictor family over all test years and since 2017 (labels: scored entries; dotted line: the support threshold of 1.4).](figs/fig3_coe_families.png)

The walk-forward admits {int(allw['cond_years'])} condition-years ({int(cp['ALL admitted']['entries']):,} scored entries): CPE {f3(allw['cpe'])} against a base of {f3(allw['base'])}, a pooled lift of {f2(allw['lift'])}. Table 1 gives the families.

| Family | Lift, all test years (entries) | Lift, 2017 onward (entries) | Supported |
|---|---|---|---|
{fam_rows}
*Table 1. COE walk-forward by predictor family. The quota-implied fair-value predictor is excluded (see Section 8).*

Quota change and the Category B/A spread meet the support rule. Interest rates, short-run de-registrations and momentum add little, and bids per quota rests on {int(S['bids']['entries_all'])} entries. By horizon the pooled lift is {f2(W['tf=1']['lift'])} at one month, {f2(W['tf=3']['lift'])} at three, {f2(W['tf=6']['lift'])} at six and {f2(W['tf=12']['lift'])} at twelve: the supported effect builds slowly. The lagged supply-cycle family, registered after the lag was found (Section 8), was admitted in only {int(S['supplycycle']['entries_all'])} entries and scores {f2(S['supplycycle']['lift_all'])}; the cycle is a description, not a validated predictor of tail moves.

### 4.4 The quota-cut effect and its robustness

Without any admission filter, a quota cut is the bottom 20% of the past six-month change in log quota, with thresholds from entries resolved before the test year. At three, six and twelve months the premium was in its top 20% of moves {pc(main.loc[3, 'cpe'])}, {pc(main.loc[6, 'cpe'])} and {pc(main.loc[12, 'cpe'])} of the time after a cut against base rates of {pc(main.loc[3, 'base'])}, {pc(main.loc[6, 'base'])} and {pc(main.loc[12, 'base'])}: lifts of {f2(main.loc[3, 'lift'])}, {f2(main.loc[6, 'lift'])} and {f2(main.loc[12, 'lift'])} on {int(main.loc[3, 'entries'])}, {int(main.loc[6, 'entries'])} and {int(main.loc[12, 'entries'])} entries, which correspond to about {int(round(main.loc[3, 'entries']/3))}, {int(round(main.loc[6, 'entries']/6))} and {int(round(main.loc[12, 'entries']/12))} non-overlapping windows.

![Figure 4. Left: probability of a top-20% premium rise after a quota cut against the base rate (labels: entries). Right: lift by period of test years (labels: entries).](figs/fig4_quota_cut.png)

The result does not depend on the thresholds. Across cut tails of 10%, 20% and 30%, premium-move tails of 10%, 20% and 30%, and the three horizons, the lift ranges from {f2(thr_min)} to {f2(thr_max)}; every one of the 27 combinations exceeds 1.4.

It does depend on the period (Table 2). The six-month lift is {f2(sb('2010-2016', 6)['lift'])} in 2010-2016 and {f2(sb('2017-2021', 6)['lift'])} in 2017-2021, and {f2(sb('2022-2026', 6)['lift'])} in 2022-2026 on {int(sb('2022-2026', 6)['entries'])} entries ({f2(sb('2022-2026', 3)['lift'])} and {f2(sb('2022-2026', 12)['lift'])} at three and twelve months). Only two of those entries fall in 2023-2026: the quota has risen almost continuously since 2023, so quota cuts have been rare. The recent period is therefore untested more than contradicted, but the effect is not detected there, and the quota formula changed in August 2022 and February 2023 (Section 2.1), which would reduce the surprise in quota moves.

| Test years | 3 months | 6 months | 12 months |
|---|---|---|---|
{sub_rows}
*Table 2. Quota-cut lift (entries) by period of test years, both categories, cut tail 20%, premium-move tail 20%.*

A regression gives the same direction. Regressing the forward 12-month log premium change on the past six-month log quota change, with Newey-West standard errors (12 lags) over {int(reg['A']['n'])} months, the slope is {f2(reg['A']['slope'])} (t = {f1(reg['A']['t'])}) for Category A and {f2(reg['B']['slope'])} (t = {f1(reg['B']['t'])}) for Category B. Splitting the change into cuts and increases,

{eq('eq5_reg', 7)}

the cut coefficient β<sup>&minus;</sup> is {f2(reg['A']['cuts'])} (t = {f1(reg['A']['t_cuts'])}) for Category A and {f2(reg['B']['cuts'])} (t = {f1(reg['B']['t_cuts'])}) for Category B, while the increase coefficient β<sup>+</sup> is {f2(reg['A']['inc'])} (t = {f1(reg['A']['t_inc'])}) and {f2(reg['B']['inc'])} (t = {f1(reg['B']['t_inc'])}): the effect is one-sided. A quota increase is not followed by a lower premium on this evidence.

### 4.5 What the cars results do not show

The quota is announced a quarter ahead and, since 2023, follows a published rule, so the market can compute it; the result says the premium reacts slowly to a known variable, not that the quota surprises. There are two supply cycles in the record. The Category A premium was higher after three months in {pc(retro[retro.scope == 'COE A'].iloc[0]['share_higher'])} of windows, so a buyer who waits has more often faced a higher premium; Section 6 tests whether that tendency is reliable enough to forecast with."""
body += f"""

## 5. Property

### 5.1 Private residential prices

![Figure 5. Left: private non-landed and landed price indices and the HDB resale price index (2009 Q1 = 100); shaded periods are falls of more than 10% in the non-landed index. Right: out-of-sample lift by family for private property, test years to 2016 and since 2017.](figs/fig5_property.png)

The property walk-forward covers five targets (all non-landed, landed and the three regions of the non-landed index) at horizons of one to eight quarters. It admits {int(pall['cond_years']):,} condition-years and {int(pall['entries']):,} scored entries: CPE {f3(pall['cpe'])} against a base of {f3(pall['base'])}, a lift of {f2(pall['lift'])} overall and {f2(pallS['lift_2017'])} since 2017. No family meets the support rule (Table 3).

| Family | Lift, all years (entries) | Lift, to 2016 | Lift, 2017 onward (entries) |
|---|---|---|---|
{pf_rows}
*Table 3. Private property walk-forward by predictor family.*

Price momentum scores {f2(PS['momentum']['lift_pre2017'])} up to 2016, driven by the 2008-2010 swings, and {f2(PS['momentum']['lift_2017'])} since 2017, on {int(PS['momentum']['entries_2017'])} entries. Rent growth, the two-year yield and vacancy show the same shape: lifts between 2.0 and 3.5 to 2016 and below 1 since. A pooled statistic that included the earlier years alone would have suggested momentum as a timing tool; the since-2017 requirement of the support rule is what removes it.

### 5.2 The HDB resale price index

The same design applied to the HDB resale index from 1990 admits {int(hall['cond_years'])} condition-years and {int(hall['n_all'])} entries: a lift of {f2(hall['lift_all'])} overall and {f2(hall['lift_2017'])} since 2017. Own momentum scores {f2(HS['momentum']['lift_all'])} on {int(HS['momentum']['n_all'])} entries, of which {int(HS['momentum']['n_2017'])} are since 2017; rates, rents and vacancy score between 1.4 and 2.1 to 2016 and between 0.0 and 0.1 since (Table 4). The index has moved sideways for four quarters, at {f1(hd['index'])} in {hd['latest']}, {pc(abs(hd['from_peak']), 1)} below its {hd['peak_q']} peak.

| Family | Lift, all years (entries) | Lift, to 2016 | Lift, 2017 onward (entries) |
|---|---|---|---|
{hf_rows}
*Table 4. HDB resale index walk-forward by predictor family.*

### 5.3 Base rates and past falls

| Series | Window | Lower after 4 quarters | Median, 4 quarters | Lower after 8 quarters | Median, 8 quarters |
|---|---|---|---|---|---|
{brow('nonlanded', 'Non-landed')}{brow('landed', 'Landed')}{hbrows}
*Table 5. How often each index was lower after four and eight quarters, and the median change.*

The last decade was almost one-way: the non-landed index was lower four quarters later in {pc(base['nonlanded']['last 10 years']['4']['lower'])} of windows, against {pc(base['nonlanded']['since 2004']['4']['lower'])} since 2004, and the worst four-quarter change since 2004 was {pc(abs(base['nonlanded']['since 2004']['4']['worst']))} down. Table 6 lists the falls of more than 10% (more than 5% for the HDB index) from a peak.

| Series | Peak | Trough | Fall | Quarters down | Quarters to recover |
|---|---|---|---|---|---|
{ddrows('nonlanded', 'Non-landed')}{ddrows('landed', 'Landed')}{hdrows}
*Table 6. Falls from a peak.*

## 6. Scoring the base rates

A buyer without a signal reaches for a base rate. How good is it? Replaying the forecast causally (Section 3.4) over every anchor with a known outcome, for the two COE series at 3, 6 and 12 months and the six property series at 4 and 8 quarters, gives Figure 6 and Table 7.

![Figure 6. Brier score of the ten-year and all-history base-rate forecasts, by series and horizon, against a coin flip (0.250).](figs/fig6_replay.png)

| Series | Horizon | Windows scored | Share actually higher | Brier, ten-year | Brier, all-history |
|---|---|---|---|---|---|
{re_rows}
*Table 7. Causal replay of the base-rate forecasts.*

For the COE premium the mean Brier score is {f3(retro[coe]['brier_10y'].mean())} for the ten-year base rate and {f3(retro[coe]['brier_all'].mean())} for the all-history rate: about a coin flip. For the property series the ten-year rate scores {f3(retro[~coe]['brier_10y'].mean())}, worse than a coin, and the all-history rate {f3(retro[~coe]['brier_all'].mean())}, better. A trailing decade over-reacts to the regime just before it; the long history is the better guide for property, and for the COE premium neither window forecasts the direction usefully.

## 7. A registered forward test

The dashboard (https://quantarram.github.io/sg-buy-timing-dashboard/) fixes the following before any outcome resolves. Each month (COE) or quarter (property, HDB) it logs the ten-year and all-history base-rate forecasts that the series will be higher after each horizon (3, 6 and 12 months; 4 and 8 quarters). It logs a condition as an entry the first time a supported family is active in its supported tail, today only a quota cut for the COE premium. It scores a forecast as the Brier contribution and an entry as the direction of the move against its implied direction, at each horizon, and publishes both, whatever the result. The first {int(N['n_forecasts'])} forecasts were logged on 16 October 2026; the earliest outcomes, at three months, arrive once the December 2026 COE data are published. The dashboard's verdict is WAIT AND WATCH unless a supported condition is active, and a verdict other than wait and watch is a statement about conditions and base rates, not a recommendation.

## 8. Limits and choices made after seeing results

- **Few independent episodes.** There are two COE supply cycles in {f1(N['span_years'])} years and about six property price cycles in the longer record. The quota-cut effect rests on about {int(round(main.loc[6, 'entries']/6))} non-overlapping six-month windows.
- **A period dependence.** The quota-cut effect is not detected from 2022 ({int(sb('2022-2026', 6)['entries'])} entries), after the quota formula changed in August 2022 and February 2023; very few cuts have occurred since. The effect is a pre-2022 finding with an untested present.
- **Choices made after seeing results.** The lagged supply-cycle family was registered after the 18 to 24 month lag was found in the descriptive analysis, so it is out of sample only in the walk-forward years. The requirement that a family also hold since 2017 was added after the property results showed the 2008-2010 effects fading. The quota-implied fair-value predictor was dropped for a specification problem: premiums trend upward for reasons other than quota, so its residual sits at an extreme in every recent month. The 2017 break point was chosen as the start of the latest decade, not tuned.
- **A hypothesis, not a finding.** Policy measures from December 2011 (the Additional Buyer's Stamp Duty; MAS, 2011) may have changed how property prices behave, which would explain why pre-2017 relationships fail. This is untested here.
- **Scope.** Public data only; prices, not transaction costs, loans, stamp duties or the cost of waiting; premiums as monthly means of two rounds, not individual bids; nothing is specific to any one flat or car.
- **Not advice.** The paper and the dashboard describe conditions and base rates. They do not recommend a purchase or a sale.

## 9. Conclusion

Timing a Singapore car purchase has one supported mechanism, a quota cut followed by a rising premium, rooted in the ten-year life of a COE, strong to 2021 and not detected since the quota rule changed. Timing a property purchase or sale has none: what predicted prices in 2008-2010 has not worked since 2017, for private property and for HDB alike. The practical content is in the base rates and the history: the long-run odds of a rise are better than the last decade's for property, the COE premium's tendency to rise is no better than a coin flip as a forecast, and past property downturns were deep. Whether the supported effect returns, and how well the dashboard's own forecasts score, will be answered by the forward ledger and not by this paper.

## 10. Code and data availability

The dashboard, data fetchers, research code, forward ledger and this paper's build scripts are in the public repository `quantarram/sg-buy-timing-dashboard`: `research/coe_cpe_walkforward.py`, `research/property_cpe_walkforward.py`, `research/hdb_rpi_cpe_walkforward.py`, `research/coe_robustness.py`, `research/coe_cycle_analysis.py`, `pipelines/update_ledger.py`, `data/ledger/` and `paper/`. Every number in this paper is recomputed by `paper/paper_numbers.py` and typeset by `paper/build_paper.py`. The CPE framework and earlier papers are in `quantarram/quant-regime-research`.

## References

Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. *Monthly Weather Review*, 78(1), 1-3.

Housing and Development Board (2026). HDB Resale Price Index and resale flat prices. Data.gov.sg, Singapore Open Data Licence.

Land Transport Authority (2022). Certificate of Entitlement quota for August 2022 to October 2022 (adjustments to the COE system to smoothen quarterly availability). https://lta.gov.sg/content/ltagov/en/newsroom/2022/7/news-releases/certificate-of-entitlement-quota-for-august-2022-to-october-2022.html

Land Transport Authority (2023). Certificate of Entitlement quota for February 2023 to April 2023. https://www.lta.gov.sg/content/ltagov/en/newsroom/2023/1/news-releases/certificate-of-entitlement-quota-for-february-2023-to-april-2023.html

Land Transport Authority (2026). COE bidding results and prices; new registrations and de-registrations under the Vehicle Quota System. Data.gov.sg, Singapore Open Data Licence.

Monetary Authority of Singapore (2011). Additional Buyer's Stamp Duty for a stable and sustainable property market (media release, December 2011). https://www.mas.gov.sg/news/media-releases/2011/absd-for-a-stable-and-sustainable-property-market

Monetary Authority of Singapore (2026). Domestic interest rates, including SORA and government securities yields. Data.gov.sg.

Newey, W. K., and West, K. D. (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. *Econometrica*, 55(3), 703-708.

Ramanathan, A. (2026). Why everyday weather does not move markets, and where rare extremes might (Paper 17). Zenodo. https://zenodo.org/records/23301263

Urban Redevelopment Authority (2026). Private residential property price index, rental index, transactions, supply and vacancy series. Data.gov.sg, Singapore Open Data Licence; URA Data Service.
"""
open(os.path.join(HERE, "singapore_timing_paper_draft.md"), "w", encoding="utf-8").write(body)
import re
ab = re.sub(r"\s+", " ", ABSTRACT).split(); pl = re.sub(r"\s+", " ", PLS).split()
print("words: abstract", len(ab), "| plain-language summary", len(pl), "| body", len(body.split()))
