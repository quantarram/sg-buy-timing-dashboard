"""Registered property predictors, computed per target price series from the quarterly panel (see research/property_cpe_walkforward.py for the mechanisms)."""
import numpy as np
import pandas as pd
from . import panel, property_panel as pp

TP = [1, 2, 4, 8]


def load():
    """All inputs on one quarterly index (Period 'Q')."""
    P = pp.prices(); R = pp.rents(); T = pp.transactions(); N = pp.new_sales(); S = pp.supply()
    gov = panel.rates()["gov2y"]; gov.index = gov.index.to_period("Q"); gov = gov.groupby(level=0).last()   # end-of-quarter two-year government yield
    return P, R, T, N, S, gov


def build_X(target, P, R, T, N, S, gov, lag_stats=1):
    """Return (log price, {(family, tau): series}, sign dict). Quarterly statistics other than price, rent and rates enter with a one-quarter lag (published after the quarter)."""
    idx = P.index
    lp = np.log(P[target]); sign = {}
    lag = lambda s: s.reindex(idx).shift(lag_stats)
    rent = np.log(R["all_wi"].reindex(idx)); g = gov.reindex(idx)
    pipe = lag(S["pipe_landed_total"] if target == "landed" else S["pipe_nonlanded_total"]); vac = lag(S["vacancy_rate"]); unsold = lag(S["unsold_total"])
    vol = lag(T[("wi", "total")]); ratio = lag(N["sold_to_launched"]).rolling(2, min_periods=1).mean()
    X = {}
    for tp in TP:
        X[("momentum", tp)] = lp - lp.shift(tp); sign["momentum"] = +1
        X[("rentgrowth", tp)] = rent - rent.shift(tp); sign["rentgrowth"] = +1
        X[("rates", tp)] = g - g.shift(tp); sign["rates"] = -1
        X[("pipeline", tp)] = np.log(pipe) - np.log(pipe.shift(tp)); sign["pipeline"] = -1
        X[("volume", tp)] = np.log(vol) - np.log(vol.shift(tp)); sign["volume"] = +1
        X[("unsold", tp)] = np.log(unsold) - np.log(unsold.shift(tp)); sign["unsold"] = -1
    ptr = lp - rent
    X[("value", 0)] = ptr - ptr.rolling(20, min_periods=12).mean(); sign["value"] = -1          # price against rent, versus its own five-year mean
    X[("vacancy", 0)] = vac - vac.rolling(20, min_periods=12).mean(); sign["vacancy"] = -1
    X[("salesratio", 0)] = ratio; sign["salesratio"] = +1
    return lp, X, sign
