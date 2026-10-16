"""Robustness of the quota-cut effect on the COE premium.
A. Without any admission filter: for each test year 2010-2026, the quota-change threshold (bottom q of the past tau_p-month change) and the premium-move threshold (top yq of the forward tau_f-month change) come only from entries resolved before 1 January of that year;
   every test-year entry in the quota tail is scored. Lift = CPE / season-matched base rate (same calendar month, all test-window entries, same thresholds). q in 10%, 20%, 30%; yq in 10%, 20%, 30%.
B. Sub-periods: test years 2010-2016, 2017-2022, 2023-2026 (the quota formula changed in 2022 and 2023).
C. A regression of the forward 12-month log premium change on the past 6-month log quota change, with Newey-West standard errors, for quota increases and cuts separately.
D. Effective sample: scored months, episodes and the count of non-overlapping tau_f windows."""
import os, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import panel
from sgtiming.predictors import build_X
Q = panel.quota_panel(); F = panel.flows(); R = panel.rates(); idx = Q['A'].index; YEARS = list(range(2010, 2027))

def run(cat, q, yq, tp, tf):
    lp, lq, X, sign = build_X(cat, Q, F, R); xs = X[('quota', tp)].values; n = len(lp); Y = (lp.shift(-tf) - lp).values; yr = idx.year.values; mo = idx.month.values; rows = []
    for year in YEARS:
        cut = int(np.searchsorted(yr, year)); tr = np.arange(0, cut - tf); te = np.where((yr == year) & (np.arange(n) < n - tf))[0]
        ytr = Y[tr]; xtr = xs[tr]; ok = ~np.isnan(xtr) & ~np.isnan(ytr)
        if ok.sum() < 48 or len(te) == 0: continue
        th = np.nanpercentile(xtr[ok], 100 * q); yth = np.nanpercentile(ytr[ok], 100 * (1 - yq))
        xte = xs[te]; yte = Y[te]; okte = ~np.isnan(xte) & ~np.isnan(yte); c = okte & (xte <= th)
        if c.sum() == 0: continue
        rows.append(dict(year=year, n=int(c.sum()), hits=int((yte[c] >= yth).sum()), months=mo[te][c].tolist(), yth=yth))
    return pd.DataFrame(rows), Y, mo, yr

def lift(rows, Y, mo, yr, cat_years=None):
    if len(rows) == 0: return (np.nan, np.nan, np.nan, 0)
    tb = 0.0; tn = 0; th = 0
    for r in rows.itertuples():
        valid = (yr >= 2010) & ~np.isnan(Y); ev = Y >= r.yth; bm = pd.Series(ev[valid]).groupby(mo[valid]).mean(); tb += float(bm.reindex(r.months).sum()); tn += r.n; th += r.hits
    return ((th / tn) / (tb / tn) if tb > 0 else np.nan, th / tn, tb / tn, tn)

print('A. NO ADMISSION FILTER: quota cut (bottom q of the past tau_p-month quota change) -> premium in its top yq of tau_f-month moves; pooled lift, both categories, tau_p = 6')
res = []
for q in (0.10, 0.20, 0.30):
    for yq in (0.10, 0.20, 0.30):
        for tf in (3, 6, 12):
            h = 0; b = 0; nn = 0
            for cat in ('A', 'B'):
                rows, Y, mo, yr = run(cat, q, yq, 6, tf)
                for r in rows.itertuples():
                    valid = (yr >= 2010) & ~np.isnan(Y); ev = Y >= r.yth; bm = pd.Series(ev[valid]).groupby(mo[valid]).mean(); b += float(bm.reindex(r.months).sum()); h += r.hits; nn += r.n
            res.append(dict(q=q, yq=yq, tf=tf, entries=nn, cpe=h / nn, base=b / nn, lift=(h / nn) / (b / nn)))
A = pd.DataFrame(res); print(A.pivot_table(index=['q', 'yq'], columns='tf', values='lift').round(2).to_string()); A.to_csv(os.path.join(ROOT, 'research', 'coe_robustness_thresholds.csv'), index=False)
print('\nlift by horizon at the main setting (q = 20%, yq = 20%):'); print(A[(A.q == 0.2) & (A.yq == 0.2)][['tf', 'entries', 'cpe', 'base', 'lift']].round(3).to_string(index=False))
print('\nB. SUB-PERIODS (q = 20%, yq = 20%, tau_p = 6), lift and entries by test years')
sub = []
for lab, ys in (('2010-2016', range(2010, 2017)), ('2017-2021', range(2017, 2022)), ('2022-2026', range(2022, 2027)), ('2023-2026', range(2023, 2027)), ('2010-2021', range(2010, 2022))):
    out = []
    for tf in (3, 6, 12):
        h = 0; b = 0; nn = 0
        for cat in ('A', 'B'):
            rows, Y, mo, yr = run(cat, 0.2, 0.2, 6, tf); rows = rows[rows.year.isin(list(ys))]
            for r in rows.itertuples():
                valid = (yr >= 2010) & ~np.isnan(Y); ev = Y >= r.yth; bm = pd.Series(ev[valid]).groupby(mo[valid]).mean(); b += float(bm.reindex(r.months).sum()); h += r.hits; nn += r.n
        out.append(f'tf={tf}: lift {(h / nn) / (b / nn) if nn and b > 0 else float("nan"):.2f} (n={nn}, CPE {h / nn if nn else float("nan"):.2f} vs {b / nn if nn else float("nan"):.2f})'); sub.append(dict(period=lab, tf=tf, entries=nn, cpe=(h / nn if nn else np.nan), base=(b / nn if nn else np.nan), lift=((h / nn) / (b / nn) if nn and b > 0 else np.nan)))
    print(f'  {lab}:', ' | '.join(out))

pd.DataFrame(sub).to_csv(os.path.join(ROOT, 'research', 'coe_robustness_subperiods.csv'), index=False)


def nw_ols(y, X, lags):
    X = np.column_stack([np.ones(len(y)), X]); b = np.linalg.lstsq(X, y, rcond=None)[0]; e = y - X @ b; Xe = X * e[:, None]; S = Xe.T @ Xe / len(y)
    for l in range(1, lags + 1):
        w = 1 - l / (lags + 1); G = Xe[l:].T @ Xe[:-l] / len(y); S += w * (G + G.T)
    XtXi = np.linalg.inv(X.T @ X / len(y)); V = XtXi @ S @ XtXi / len(y); return b, np.sqrt(np.diag(V))
print('\nC. REGRESSION: forward 12-month log premium change on the past 6-month log quota change (Newey-West, 12 lags), 2002-2026')
rg = []
for cat in ('A', 'B'):
    lp, lq, X, sign = build_X(cat, Q, F, R); dq = X[('quota', 6)]; y = (lp.shift(-12) - lp); d = pd.DataFrame({'y': y, 'dq': dq}).dropna()
    b, se = nw_ols(d.y.values, d.dq.values, 12); print(f'  Category {cat}: slope {b[1]:+.2f} (t {b[1] / se[1]:+.1f}), n={len(d)}, R2 {1 - ((d.y - (b[0] + b[1] * d.dq)) ** 2).sum() / ((d.y - d.y.mean()) ** 2).sum():.3f}')
    dd = d.assign(cut=np.minimum(d.dq, 0), up=np.maximum(d.dq, 0)); Xc = dd[['cut', 'up']].values; b2, se2 = nw_ols(dd.y.values, Xc, 12)
    print(f'     split: cuts slope {b2[1]:+.2f} (t {b2[1] / se2[1]:+.1f}), increases slope {b2[2]:+.2f} (t {b2[2] / se2[2]:+.1f}); post-2010 only: ', end='')
    d2 = dd[dd.index >= '2010-01-01']; b3, se3 = nw_ols(d2.y.values, d2[['cut', 'up']].values, 12); print(f'cuts {b3[1]:+.2f} (t {b3[1] / se3[1]:+.1f}), increases {b3[2]:+.2f} (t {b3[2] / se3[2]:+.1f}), n={len(d2)}')
    rg.append(dict(cat=cat, slope=b[1], t=b[1] / se[1], cuts=b2[1], t_cuts=b2[1] / se2[1], inc=b2[2], t_inc=b2[2] / se2[2], n=len(d)))
pd.DataFrame(rg).to_csv(os.path.join(ROOT, 'research', 'coe_robustness_regression.csv'), index=False)
print('\nD. EFFECTIVE SAMPLE at the main setting: scored months, quota-cut episodes (entries more than tau_f months apart) and non-overlapping tau_f windows')
for tf in (3, 6, 12):
    ent = []
    for cat in ('A', 'B'):
        rows, Y, mo, yr = run(cat, 0.2, 0.2, 6, tf); ent.append(rows.n.sum())
    print(f'  tau_f={tf}: scored entries {sum(ent)} over two categories -> about {sum(ent) / tf:.0f} non-overlapping windows')
