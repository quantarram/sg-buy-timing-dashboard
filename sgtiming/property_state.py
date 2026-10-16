"""Descriptive property state used by the research notes and the dashboard: base rates of forward price changes, drawdown history and the current position of each indicator."""
import numpy as np
import pandas as pd

NAMES = {"nonlanded": "Condo (non-landed, all regions)", "nl_ccr": "Condo, core central", "nl_rcr": "Condo, rest of central", "nl_ocr": "Condo, outside central", "landed": "Landed"}


def base_rates(P, targets=NAMES, horizons=(4, 8), recent_from="2016Q3"):
    out = {}
    for t in targets:
        lp = np.log(P[t].dropna()); out[t] = {}
        for lab, start in (("since 2004", pd.Period("2004Q1")), ("last 10 years", pd.Period(recent_from))):
            sub = lp[lp.index >= start]; out[t][lab] = {}
            for h in horizons:
                ch = (lp.shift(-h) - lp)[sub.index].dropna()
                out[t][lab][h] = dict(n=len(ch), lower=float((ch < 0).mean()), dn5=float((ch < -0.05).mean()), up5=float((ch > 0.05).mean()), med=float(np.median(ch)), worst=float(ch.min()))
    return out


def drawdowns(series, min_depth=0.10):
    """Peak-to-trough episodes deeper than min_depth: (peak quarter, trough quarter, depth, quarters peak to trough, quarters trough back to the old peak or None)."""
    s = series.dropna(); eps = []; peak_i = 0; i = 0; n = len(s)
    while i < n:
        if s.iloc[i] >= s.iloc[peak_i]: peak_i = i; i += 1; continue
        j = i; trough_i = i
        while j < n and s.iloc[j] < s.iloc[peak_i]:
            if s.iloc[j] < s.iloc[trough_i]: trough_i = j
            j += 1
        depth = s.iloc[trough_i] / s.iloc[peak_i] - 1
        if depth <= -min_depth: eps.append((str(s.index[peak_i]), str(s.index[trough_i]), float(depth), trough_i - peak_i, (j - trough_i) if j < n else None))
        peak_i = j if j < n else peak_i; i = j + 1 if j < n else n
    return eps


def indicators(P, R, T, N, S):
    """Current state: price change, distance from peak, price-to-rent and vacancy against their own history, sales rate, unsold stock."""
    rows = []
    rent = np.log(R["all_wi"])
    for t, nm in NAMES.items():
        p = P[t].dropna(); lpv = np.log(p); ptr = (lpv - rent.reindex(p.index)).dropna()
        rows.append(dict(key=t, name=nm, index=float(p.iloc[-1]), yoy=float(p.iloc[-1] / p.iloc[-5] - 1), qoq=float(p.iloc[-1] / p.iloc[-2] - 1), from_peak=float(p.iloc[-1] / p.max() - 1), peak_q=str(p.idxmax()), ptr_pct=float((ptr.iloc[:-1] < ptr.iloc[-1]).mean() * 100)))
    v = S["vacancy_rate"].dropna(); sr = N["sold_to_launched"].dropna(); u = S["unsold_total"].dropna()
    extra = dict(vacancy=float(v.iloc[-1]), vacancy_pct=float((v.iloc[:-1] < v.iloc[-1]).mean() * 100), sold_to_launched=float(sr.iloc[-1]), unsold=float(u.iloc[-1]), unsold_pct=float((u.iloc[:-1] < u.iloc[-1]).mean() * 100),
                 txn_total=float(T[("wi", "total")].iloc[-1]), txn_yoy=float(T[("wi", "total")].iloc[-1] / T[("wi", "total")].iloc[-5] - 1), new_sale=float(T[("wi", "new_sale")].iloc[-1]), resale=float(T[("wi", "resale")].iloc[-1]),
                 pipeline_nonlanded=float(S["pipe_nonlanded_total"].dropna().iloc[-1]), last_q=str(P.index[-1]))
    return rows, extra
