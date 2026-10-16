"""COE premium (Category A and B, old definitions: up to 1,600cc and 97kW / above), monthly 2002-02 to 2026-09: causal CPE walk-forward.

Target Y: forward log change of the monthly premium (mean of the two bidding rounds) over tau_f = 1, 3, 6 months; event 'higher' = top 20%, 'lower' = bottom 20% of Y.
Predictors X (mechanism registered before any result; sign +1 = high X means premium higher, -1 = lower):
  quota    : change in log quota over tau_p months                                   -1  (more supply)
  dereg    : de-registrations (lagged 2 months, published with delay), rolling tau_p vs 12 months   -1  (feeds next quarters' quota)
  bids     : bids received / quota, rolling tau_p months                              +1  (demand pressure)
  rates    : change in the 2-year government bond yield over tau_p months (lagged 1)   -1  (dearer financing)
  value    : log premium minus its trailing 12-month mean                             -1  (reversion)
  fair     : log premium minus a quota-implied level (log premium on log 12-month quota, refit each year on past data)  -1
  spread   : log(B/A) minus its trailing 12-month mean; +1 for A (A cheap against B), -1 for B
  momentum : change in log premium over tau_p months                                  +1  (continuation)
tau_p in 1, 3, 6, 12 where it applies; X tails q = 20% and 10% on each side.
Walk-forward: for each test year 2010..2026, only entries whose outcome had resolved before 1 January of that year are used to set X and Y thresholds
(all earlier data) and to admit conditions (lift >= 1.5, >= 20 entries, >= 4 episodes of entries more than tau_f months apart; base rate matched on calendar month).
Admitted conditions are scored on that year's entries. Pooled over years: CPE, season-matched base (same calendar months over the whole test window), lift.
Windows overlap (every month is an entry); episodes are reported next to entry counts."""
import os, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import panel

Q = panel.quota_panel(); F = panel.flows(); R = panel.rates(); idx = Q['A'].index
TP = [1, 3, 6, 12]; TF = [1, 3, 6]; QS = [0.20, 0.10]; YEARS = list(range(2010, 2027)); LAGD = 2


def build_X(cat):
    d = Q[cat]; other = 'B' if cat == 'A' else 'A'
    lp = np.log(d['premium']); lq = np.log(d['quota']); ratio = d['bids'] / d['quota']
    dereg = F['dereg_' + cat].reindex(idx).shift(LAGD); gov = R['gov2y'].reindex(idx).shift(1)
    spread = (np.log(Q['B']['premium']) - np.log(Q['A']['premium'])); sp_dev = spread - spread.rolling(12, min_periods=9).mean()
    X = {}; SIGN = {'quota': -1, 'dereg': -1, 'bids': +1, 'rates': -1, 'value': -1, 'fair': -1, 'spread': (+1 if cat == 'A' else -1), 'momentum': +1}
    for tp in TP:
        X[('quota', tp)] = lq - lq.shift(tp)
        X[('dereg', tp)] = np.log(dereg.rolling(tp, min_periods=max(1, tp // 2)).mean()) - np.log(dereg.rolling(12, min_periods=9).mean())
        X[('bids', tp)] = ratio.rolling(tp, min_periods=max(1, tp // 2)).mean()
        X[('rates', tp)] = gov - gov.shift(tp)
        X[('momentum', tp)] = lp - lp.shift(tp)
    X[('value', 0)] = lp - lp.rolling(12, min_periods=9).mean(); X[('spread', 0)] = sp_dev
    return lp, lq, X, SIGN


def fair_resid(lp, lq, year):
    """Residual of log premium against the log 12-month mean quota, fitted only on months before the given year."""
    lq12 = lq.rolling(12, min_periods=9).mean(); tr = (lp.index < pd.Timestamp(f'{year}-01-01')) & lq12.notna() & lp.notna()
    if tr.sum() < 36: return pd.Series(np.nan, index=lp.index)
    b = np.polyfit(lq12[tr], lp[tr], 1); return lp - (b[0] * lq12 + b[1])


def episodes(pos, gap):
    pos = np.sort(pos); return 0 if len(pos) == 0 else 1 + int((np.diff(pos) > gap).sum())


rows = []
for cat in ['A', 'B']:
    lp, lq, X, SIGN = build_X(cat); n = len(lp); t = lp.index; mo = t.month.values; yr = t.year.values
    for tf in TF:
        Y = (lp.shift(-tf) - lp).values; known_until = n - tf         # Y valid for positions < n - tf
        for (fam, tp), xs0 in list(X.items()) + [(('fair', 0), None)]:
            for year in YEARS:
                xs = (fair_resid(lp, lq, year) if fam == 'fair' else xs0).values
                cut = int(np.searchsorted(t.values, np.datetime64(f'{year}-01-01')))      # first position of the test year
                tr = np.arange(0, cut - tf)                                               # entries whose outcome resolved before the test year
                te = np.where((yr == year) & (np.arange(n) < known_until))[0]
                if len(tr) < 60 or len(te) == 0: continue
                ytr = Y[tr]; y80, y20 = np.nanpercentile(ytr, 80), np.nanpercentile(ytr, 20)
                xtr = xs[tr]; ok = ~np.isnan(xtr) & ~np.isnan(ytr)
                if ok.sum() < 48: continue
                for q in QS:
                    for side in ('high', 'low'):
                        th = np.nanpercentile(xtr[ok], 100 * (1 - q) if side == 'high' else 100 * q)
                        cond_tr = ok & ((xtr >= th) if side == 'high' else (xtr <= th))
                        implies_up = (SIGN[fam] > 0) == (side == 'high'); ev = (ytr >= y80) if implies_up else (ytr <= y20)
                        ntr = int(cond_tr.sum())
                        if ntr < 20: continue
                        # season-matched base on training entries: mean over the calendar months of the conditioned entries
                        bm = pd.Series(ev[ok]).groupby(mo[tr][ok]).mean(); base_tr = float(bm.reindex(mo[tr][cond_tr]).mean()); cpe_tr = float(ev[cond_tr].mean())
                        lift_tr = cpe_tr / base_tr if base_tr > 0 else np.nan; ep = episodes(np.where(cond_tr)[0], tf)
                        if not (lift_tr >= 1.5 and ep >= 4): continue
                        xte = xs[te]; yte = Y[te]; okte = ~np.isnan(xte) & ~np.isnan(yte)
                        cond_te = okte & ((xte >= th) if side == 'high' else (xte <= th))
                        if cond_te.sum() == 0: continue
                        evte = (yte >= y80) if implies_up else (yte <= y20)
                        rows.append(dict(cat=cat, fam=fam, tp=tp, tf=tf, q=q, side=side, year=year, implies='higher' if implies_up else 'lower', n_tr=ntr, ep_tr=ep, lift_tr=lift_tr, n_te=int(cond_te.sum()), hits=int(evte[cond_te].sum()), mo_te=mo[te][cond_te].tolist(), y80=y80, y20=y20))
S = pd.DataFrame(rows)
print('admitted condition-years:', len(S), '| distinct conditions:', S[['cat', 'fam', 'tp', 'tf', 'q', 'side']].drop_duplicates().shape[0])
# season-matched base: see pooled_base below
def pooled_base(g):
    """Mean over scored entries of the base rate of the event in that calendar month (all 2010+ entries, same thresholds)."""
    tot_b, tot_n = 0.0, 0
    for r in g.itertuples():
        lp = np.log(Q[r.cat]['premium']); Y = (lp.shift(-r.tf) - lp); mo = lp.index.month.values; yr = lp.index.year.values
        valid = (yr >= 2010) & Y.notna().values
        ev = (Y.values >= r.y80) if r.implies == 'higher' else (Y.values <= r.y20)
        bm = pd.Series(ev[valid]).groupby(mo[valid]).mean()
        tot_b += float(bm.reindex(r.mo_te).sum()); tot_n += r.n_te
    return tot_b, tot_n
def summarise(g, label):
    b, n = pooled_base(g); h = g.hits.sum()
    return dict(group=label, cond_years=len(g), entries=int(n), cpe=h / n, base=b / n, lift=(h / n) / (b / n) if b > 0 else np.nan)
out = []
out.append(summarise(S, 'ALL admitted'))
for k in ['fam', 'tf', 'q', 'cat', 'side', 'year']:
    for v, g in S.groupby(k): out.append(summarise(g, f'{k}={v}'))
T = pd.DataFrame(out); pd.set_option('display.width', 200); print(T.round(3).to_string(index=False))
T.to_csv(os.path.join(ROOT, 'research', 'coe_walkforward_summary.csv'), index=False); S.drop(columns=['mo_te']).to_csv(os.path.join(ROOT, 'research', 'coe_walkforward_admitted.csv'), index=False)
