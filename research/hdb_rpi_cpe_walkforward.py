"""CPE walk-forward on the HDB Resale Price Index (quarterly, 1990 Q1 onward), the national resale price level.
Target: forward log change over 1, 2, 4, 8 quarters (events: top 20% 'higher', bottom 20% 'lower'). Same causal walk-forward and support rule as the rest of the dashboard.
Registered mechanisms (+1 = high X means prices higher): momentum (own change) +1; privmom (outside-central private price index change, an upgrader channel) +1; rel (log HDB / private OCR minus its 5-year mean) -1;
rates (2-year government yield change) -1; rentgrowth (private rental index change) +1; volume (private units transacted change) +1; pipeline (private supply pipeline change) -1; vacancy (private vacancy rate minus its 5-year mean) -1.
Statistics other than index prices, rents and rates enter with a one-quarter lag. Writes research/hdb_rpi_family_support.csv and research/hdb_rpi_state.json."""
import json, os, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import property_predictors as pr, property_panel as pp, property_state as ps

P, R, T, N, S, gov = pr.load(); hdb = pp.hdb_rpi(); P['hdb'] = hdb.reindex(P.index)
lp, X, SIGN = pr.build_X('hdb', P, R, T, N, S, gov)
for k in [('unsold', t) for t in pr.TP] + [('value', 0), ('salesratio', 0)]: X.pop(k, None)
for f in ('unsold', 'value', 'salesratio'): SIGN.pop(f, None)
ocr = np.log(P['nl_ocr'])
for tp in pr.TP: X[('privmom', tp)] = (ocr - ocr.shift(tp)).reindex(P.index); SIGN['privmom'] = +1
rel = lp - ocr; X[('rel', 0)] = rel - rel.rolling(20, min_periods=12).mean(); SIGN['rel'] = -1
lp = lp.dropna(); idx = lp.index; n = len(lp); qy = np.array([p.quarter for p in idx]); yr = np.array([p.year for p in idx]); X = {k: v.reindex(idx) for k, v in X.items()}
TF = [1, 2, 4, 8]; QS = [0.20, 0.10]; YEARS = list(range(2000, 2027))


def episodes(pos, gap):
    pos = np.sort(pos); return 0 if len(pos) == 0 else 1 + int((np.diff(pos) > gap).sum())


rows = []
for tf in TF:
    Y = (lp.shift(-tf) - lp).values; known = n - tf
    for (fam, tp), xs0 in X.items():
        xs = xs0.values
        for year in YEARS:
            cut = int(np.searchsorted(yr, year)); tr = np.arange(0, cut - tf); te = np.where((yr == year) & (np.arange(n) < known))[0]
            if len(tr) < 40 or len(te) == 0: continue
            ytr = Y[tr]; xtr = xs[tr]; ok = ~np.isnan(xtr) & ~np.isnan(ytr)
            if ok.sum() < 32: continue
            y80, y20 = np.nanpercentile(ytr[ok], 80), np.nanpercentile(ytr[ok], 20)
            for q in QS:
                for side in ('high', 'low'):
                    th = np.nanpercentile(xtr[ok], 100 * (1 - q) if side == 'high' else 100 * q)
                    cond = ok & ((xtr >= th) if side == 'high' else (xtr <= th)); ntr = int(cond.sum())
                    if ntr < 12: continue
                    up = (SIGN[fam] > 0) == (side == 'high'); ev = (ytr >= y80) if up else (ytr <= y20)
                    bm = pd.Series(ev[ok]).groupby(qy[tr][ok]).mean(); base = float(bm.reindex(qy[tr][cond]).mean()); cpe = float(ev[cond].mean()); lift = cpe / base if base > 0 else np.nan; ep = episodes(np.where(cond)[0], tf)
                    if not (lift >= 1.5 and ep >= 4): continue
                    xte = xs[te]; yte = Y[te]; okte = ~np.isnan(xte) & ~np.isnan(yte); ct = okte & ((xte >= th) if side == 'high' else (xte <= th))
                    if ct.sum() == 0: continue
                    evte = (yte >= y80) if up else (yte <= y20)
                    rows.append(dict(fam=fam, tp=tp, tf=tf, q=q, side=side, year=year, implies='higher' if up else 'lower', n_te=int(ct.sum()), hits=int(evte[ct].sum()), qt_te=qy[te][ct].tolist(), y80=y80, y20=y20))
W = pd.DataFrame(rows); print('admitted condition-years', len(W), '| distinct conditions', W[['fam', 'tp', 'tf', 'q', 'side']].drop_duplicates().shape[0])


def pooled(g):
    tb = 0.0; tn = 0; cache = {}
    for r in g.itertuples():
        key = (r.tf, r.y80, r.y20, r.implies)
        if key not in cache:
            Yv = (lp.shift(-r.tf) - lp); valid = (yr >= 2000) & Yv.notna().values; ev = (Yv.values >= r.y80) if r.implies == 'higher' else (Yv.values <= r.y20); cache[key] = pd.Series(ev[valid]).groupby(qy[valid]).mean()
        tb += float(cache[key].reindex(r.qt_te).sum()); tn += r.n_te
    return tb, tn


def lift(g):
    if len(g) == 0: return (np.nan, 0)
    b, nn = pooled(g); return ((g.hits.sum() / nn) / (b / nn) if b > 0 else np.nan, int(nn))


sup = []
for fam, g in list(W.groupby('fam')) + [('ALL', W)]:
    a = lift(g); r = lift(g[g.year >= 2017]); e = lift(g[g.year <= 2016]); sup.append(dict(family=fam, lift_all=a[0], n_all=a[1], lift_2017=r[0], n_2017=r[1], lift_pre2017=e[0], n_pre2017=e[1], cond_years=len(g)))
    print(f'  {fam:11s} all {a[0]:5.2f} [{a[1]:4d}] | 2017+ {r[0]:5.2f} [{r[1]:4d}] | to 2016 {e[0]:5.2f} [{e[1]:4d}]')
pd.DataFrame(sup).to_csv(os.path.join(ROOT, 'research', 'hdb_rpi_family_support.csv'), index=False)
# descriptive state
chg = {h: (lp.shift(-h) - lp).dropna() for h in (2, 4, 8)}; base = {}
for lab, start in (('since 1990', idx[0]), ('since 2004', pd.Period('2004Q1')), ('last 10 years', pd.Period('2016Q3'))):
    base[lab] = {str(h): dict(lower=float((c[c.index >= start] < 0).mean()), med=float(np.median(c[c.index >= start])), p10=float(np.percentile(c[c.index >= start], 10)), p90=float(np.percentile(c[c.index >= start], 90))) for h, c in chg.items()}
c4 = lp - lp.shift(4); f4 = lp.shift(-4) - lp; f8 = lp.shift(-8) - lp; flat = (c4.abs() <= 0.015) & f4.notna(); eps = []; cur = []
for q, v in flat.items():
    if v: cur.append(q)
    elif cur: eps.append(cur); cur = []
if cur: eps.append(cur)
spells = [dict(start=str(e[0]), end=str(e[-1]), quarters=len(e), next4_first=float(f4[e[0]]), next4_last=float(f4[e[-1]])) for e in eps]
dd = [dict(peak=a, trough=b, depth=float(d), down=int(q1), recover=(None if q2 is None else int(q2))) for a, b, d, q1, q2 in ps.drawdowns(hdb, 0.05)]
state = dict(latest=str(hdb.index[-1]), index=float(hdb.iloc[-1]), peak=float(hdb.max()), peak_q=str(hdb.idxmax()), yoy=float(hdb.iloc[-1] / hdb.iloc[-5] - 1), from_peak=float(hdb.iloc[-1] / hdb.max() - 1), base=base, drawdowns=dd, flat_spells=spells,
             flat_summary=dict(n_quarters=int(flat.sum()), n_spells=len(eps), next4_median=float(np.median(f4[flat])), next4_lower=float(np.mean(f4[flat] < 0)), next8_median=float(np.nanmedian(f8[flat])), next8_lower=float((f8[flat].dropna() < 0).mean())), now_change4=float(c4.iloc[-1]))
json.dump(state, open(os.path.join(ROOT, 'research', 'hdb_rpi_state.json'), 'w'), indent=1)
print('state:', {k: state[k] for k in ('latest', 'index', 'peak', 'peak_q', 'yoy', 'from_peak')})
