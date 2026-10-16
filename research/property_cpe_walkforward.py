"""Private residential price index (all non-landed, landed, and non-landed by region), quarterly: causal CPE walk-forward.

Target Y: forward log change of the price index over tau_f = 1, 2, 4, 8 quarters; event 'higher' = top 20%, 'lower' = bottom 20% of Y.
Predictors (mechanism registered before any result; sign +1 = high X means prices higher, -1 = lower):
  momentum  : price change over tau_p quarters                                        +1  (continuation)
  rentgrowth: change in the whole-island rental index over tau_p quarters             +1  (rents lead or confirm demand)
  rates     : change in the 2-year government bond yield over tau_p quarters          -1  (dearer mortgages)
  pipeline  : change in the supply pipeline (landed or non-landed) over tau_p quarters -1 (more supply)
  volume    : change in units transacted (whole island)                                +1  (demand)
  unsold    : change in unsold approved units                                          -1  (overhang)
  value     : log price-to-rent, minus its own trailing five-year mean                 -1  (reversion)
  vacancy   : vacancy rate minus its own trailing five-year mean                       -1  (slack)
  salesratio: uncompleted units sold / launched (two-quarter mean)                     +1  (new-sale demand)
Statistics other than price, rent and rates enter with a one-quarter lag (published after the quarter).
Walk-forward: for each test year the X and Y thresholds and the admission (lift >= 1.5, >= 20 entries, >= 4 episodes of entries more than tau_f quarters apart, base rate matched on the quarter of the year) use only entries whose outcome had resolved before 1 January of that year. Pooled scoring against the same-quarter base rate over the test window."""
import os, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import property_predictors as pr

P, R, T, N, S, gov = pr.load()
TARGETS = ['nonlanded', 'landed', 'nl_ccr', 'nl_rcr', 'nl_ocr']; TF = [1, 2, 4, 8]; QS = [0.20, 0.10]; YEARS = list(range(2005, 2027))
START = {'nonlanded': 1975, 'landed': 1975, 'nl_ccr': 2004, 'nl_rcr': 2004, 'nl_ocr': 2004}


def episodes(pos, gap):
    pos = np.sort(pos); return 0 if len(pos) == 0 else 1 + int((np.diff(pos) > gap).sum())


rows = []
for tgt in TARGETS:
    lp, X, SIGN = pr.build_X(tgt, P, R, T, N, S, gov); lp = lp.dropna(); idx = lp.index; n = len(lp); qy = np.array([p.quarter for p in idx]); yr = np.array([p.year for p in idx])
    X = {k: v.reindex(idx) for k, v in X.items()}
    for tf in TF:
        Y = (lp.shift(-tf) - lp).values; known_until = n - tf
        for (fam, tp), xs0 in X.items():
            xs = xs0.values
            for year in YEARS:
                cut = int(np.searchsorted(yr, year)); tr = np.arange(0, cut - tf); te = np.where((yr == year) & (np.arange(n) < known_until))[0]
                if len(tr) < 40 or len(te) == 0: continue
                ytr = Y[tr]; xtr = xs[tr]; ok = ~np.isnan(xtr) & ~np.isnan(ytr)
                if ok.sum() < 32: continue
                y80, y20 = np.nanpercentile(ytr[ok], 80), np.nanpercentile(ytr[ok], 20)
                for q in QS:
                    for side in ('high', 'low'):
                        th = np.nanpercentile(xtr[ok], 100 * (1 - q) if side == 'high' else 100 * q)
                        cond_tr = ok & ((xtr >= th) if side == 'high' else (xtr <= th)); ntr = int(cond_tr.sum())
                        if ntr < 12: continue
                        implies_up = (SIGN[fam] > 0) == (side == 'high'); ev = (ytr >= y80) if implies_up else (ytr <= y20)
                        bm = pd.Series(ev[ok]).groupby(qy[tr][ok]).mean(); base_tr = float(bm.reindex(qy[tr][cond_tr]).mean()); cpe_tr = float(ev[cond_tr].mean())
                        lift_tr = cpe_tr / base_tr if base_tr > 0 else np.nan; ep = episodes(np.where(cond_tr)[0], tf)
                        if not (lift_tr >= 1.5 and ep >= 4): continue
                        xte = xs[te]; yte = Y[te]; okte = ~np.isnan(xte) & ~np.isnan(yte); cond_te = okte & ((xte >= th) if side == 'high' else (xte <= th))
                        if cond_te.sum() == 0: continue
                        evte = (yte >= y80) if implies_up else (yte <= y20)
                        rows.append(dict(tgt=tgt, fam=fam, tp=tp, tf=tf, q=q, side=side, year=year, implies='higher' if implies_up else 'lower', n_tr=ntr, ep_tr=ep, lift_tr=lift_tr, n_te=int(cond_te.sum()), hits=int(evte[cond_te].sum()), qt_te=qy[te][cond_te].tolist(), y80=y80, y20=y20))
S_ = pd.DataFrame(rows)
print('admitted condition-years:', len(S_), '| distinct conditions:', S_[['tgt', 'fam', 'tp', 'tf', 'q', 'side']].drop_duplicates().shape[0])


def pooled_base(g):
    tot_b, tot_n = 0.0, 0; cache = {}
    for r in g.itertuples():
        key = (r.tgt, r.tf, r.y80, r.y20, r.implies)
        if key not in cache:
            lp = np.log(P[r.tgt]).dropna(); Y = (lp.shift(-r.tf) - lp); qy = np.array([p.quarter for p in lp.index]); yr = np.array([p.year for p in lp.index])
            valid = (yr >= 2005) & Y.notna().values; ev = (Y.values >= r.y80) if r.implies == 'higher' else (Y.values <= r.y20)
            cache[key] = pd.Series(ev[valid]).groupby(qy[valid]).mean()
        tot_b += float(cache[key].reindex(r.qt_te).sum()); tot_n += r.n_te
    return tot_b, tot_n


def summarise(g, label):
    b, n = pooled_base(g); h = g.hits.sum()
    return dict(group=label, cond_years=len(g), entries=int(n), cpe=h / n, base=b / n, lift=(h / n) / (b / n) if b > 0 else np.nan)


if len(S_):
    out = [summarise(S_, 'ALL admitted')]
    for k in ['fam', 'tf', 'q', 'tgt', 'side', 'implies']:
        for v, g in S_.groupby(k): out.append(summarise(g, f'{k}={v}'))
    T_ = pd.DataFrame(out); pd.set_option('display.width', 200); print(T_.round(3).to_string(index=False))
    T_.to_csv(os.path.join(ROOT, 'research', 'property_walkforward_summary.csv'), index=False); S_.drop(columns='qt_te').to_csv(os.path.join(ROOT, 'research', 'property_walkforward_admitted.csv'), index=False)

# ---- family support table used by the dashboard: lift over all test years and over 2017 onward
def _lift(g):
    if len(g) == 0: return (np.nan, 0)
    b, n = pooled_base(g); h = g.hits.sum(); return ((h / n) / (b / n) if b > 0 else np.nan, int(n))
sup = []
for fam, g in list(S_.groupby('fam')) + [('ALL', S_)]:
    a = _lift(g); r = _lift(g[g.year >= 2017]); e = _lift(g[g.year <= 2016]); sup.append(dict(family=fam, lift_all=a[0], entries_all=a[1], lift_2017=r[0], entries_2017=r[1], lift_pre2017=e[0], entries_pre2017=e[1], cond_years=len(g)))
pd.DataFrame(sup).to_csv(os.path.join(ROOT, 'research', 'property_family_support.csv'), index=False)
