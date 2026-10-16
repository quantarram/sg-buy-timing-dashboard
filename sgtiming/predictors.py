"""The registered COE predictors (see research/coe_cpe_walkforward.py for the mechanisms) computed from the monthly panel."""
import numpy as np
import pandas as pd

TP = [1, 3, 6, 12]
SIGN_BASE = {"quota": -1, "dereg": -1, "bids": +1, "rates": -1, "value": -1, "fair": -1, "supplycycle": -1, "momentum": +1}


def build_X(cat, Q, F, R, lagd=2):
    """Return (log premium, log quota, dict {(family, tau_p): series}, sign dict) for category 'A' or 'B'."""
    idx = Q["A"].index
    d = Q[cat]
    lp = np.log(d["premium"]); lq = np.log(d["quota"]); ratio = d["bids"] / d["quota"]
    dereg = F["dereg_" + cat].reindex(idx).shift(lagd); gov = R["gov2y"].reindex(idx).shift(1)
    spread = np.log(Q["B"]["premium"]) - np.log(Q["A"]["premium"]); sp_dev = spread - spread.rolling(12, min_periods=9).mean()
    sign = dict(SIGN_BASE); sign["spread"] = +1 if cat == "A" else -1
    X = {}
    for tp in TP:
        X[("quota", tp)] = lq - lq.shift(tp)
        X[("dereg", tp)] = np.log(dereg.rolling(tp, min_periods=max(1, tp // 2)).mean()) - np.log(dereg.rolling(12, min_periods=9).mean())
        X[("bids", tp)] = ratio.rolling(tp, min_periods=max(1, tp // 2)).mean()
        X[("rates", tp)] = gov - gov.shift(tp)
        X[("momentum", tp)] = lp - lp.shift(tp)
    sc = np.log(dereg.rolling(12, min_periods=9).mean())
    for L in (6, 12, 18):
        X[("supplycycle", L)] = sc.shift(L) - sc.shift(L + 12)
    X[("value", 0)] = lp - lp.rolling(12, min_periods=9).mean(); X[("spread", 0)] = sp_dev
    return lp, lq, X, sign


def fair_resid(lp, lq, year):
    """Residual of log premium against the log 12-month mean quota, fitted only on months before the given year."""
    lq12 = lq.rolling(12, min_periods=9).mean(); tr = (lp.index < pd.Timestamp(f"{year}-01-01")) & lq12.notna() & lp.notna()
    if tr.sum() < 36:
        return pd.Series(np.nan, index=lp.index)
    b = np.polyfit(lq12[tr], lp[tr], 1)
    return lp - (b[0] * lq12 + b[1])
