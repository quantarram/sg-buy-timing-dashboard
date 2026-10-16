"""Forward ledger and causal scoring of the dashboard's statements.

Two things are logged and scored as outcomes arrive:
  * base-rate forecasts: for each scope and horizon, the share of the last ten years' (and of all) windows in which the series was higher after the horizon, as known at the anchor period;
  * entries: each time a supported condition becomes active, with its implied direction.
A replay of the base-rate forecast over the past (causal: only windows already finished at each anchor) shows how well it would have scored.
Scopes: COE A and B (monthly mean premium; horizons 3, 6, 12 months); private price indices and the HDB resale index (quarterly; horizons 4, 8 quarters).
"""
import json, os
import numpy as np
import pandas as pd
from . import panel, property_panel as pp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "data", "ledger")
START = "2026-10-16"
COE_H = (3, 6, 12); Q_H = (4, 8)
QSCOPES = {"nonlanded": "Condo (non-landed)", "landed": "Landed", "nl_ccr": "Condo, core central", "nl_rcr": "Condo, rest of central", "nl_ocr": "Condo, outside central", "hdb": "HDB resale index"}


def series():
    """{scope: (Series indexed by Period or Timestamp, unit, horizons, window length for the ten-year base rate)}"""
    out = {}
    Q = panel.quota_panel()
    for c in ("A", "B"):
        s = Q[c]["premium"].dropna(); out[f"COE {c}"] = (s, "month", COE_H, 120)
    P = pp.prices(); h = pp.hdb_rpi()
    for k, nm in QSCOPES.items():
        s = (h if k == "hdb" else P[k]).dropna(); out[nm] = (s, "quarter", Q_H, 40)
    return out


def _shift(idx, i, h, unit):
    return idx[i + h] if i + h < len(idx) else None


def base_rate(s, a, h, win):
    """Share of windows (start s0, outcome s0+h) with the outcome known at position a, starting within the last `win` periods, in which the series was higher; also over all windows."""
    v = s.values; n = a + 1
    starts = np.arange(0, n - h)                                    # outcome position s0 + h <= a
    ch = v[starts + h] - v[starts]
    recent = starts >= (a - h - win)
    return (float((ch[recent] > 0).mean()) if recent.any() else np.nan, int(recent.sum()), float((ch > 0).mean()) if len(ch) else np.nan, int(len(ch)))


def retrospective(sc):
    """Causal replay of the base-rate forecast over every anchor with a known outcome."""
    rows = []
    for scope, (s, unit, hs, win) in sc.items():
        v = s.values
        for h in hs:
            lo = 120 if unit == "month" else 40                       # first anchor once ten years of history exist
            res = []
            for a in range(lo, len(v) - h):
                p10, n10, pall, nall = base_rate(s, a, h, win)
                if np.isnan(p10): continue
                o = float(v[a + h] > v[a]); res.append((p10, pall, o))
            if not res: continue
            r = np.array(res); o = r[:, 2]
            rows.append(dict(scope=scope, horizon=h, unit=unit, n=len(r), share_higher=o.mean(), brier_10y=float(np.mean((r[:, 0] - o) ** 2)), brier_all=float(np.mean((r[:, 1] - o) ** 2)), brier_coin=0.25, brier_always_higher=float(np.mean((1 - o) ** 2)),
                             hit_10y=float(np.mean((r[:, 0] > 0.5) == (o == 1)))))
    return pd.DataFrame(rows)


def _read(name, cols):
    p = os.path.join(LEDGER, name)
    return pd.read_csv(p, dtype=str) if os.path.exists(p) else pd.DataFrame(columns=cols)


FC_COLS = ["id", "logged", "scope", "anchor", "unit", "horizon", "p_10y", "n_10y", "p_all", "anchor_value"]
EN_COLS = ["id", "logged", "scope", "family", "tau", "tail", "implied", "anchor", "unit", "anchor_value"]
RS_COLS = ["kind", "id", "scope", "anchor", "horizon", "unit", "outcome_period", "anchor_value", "outcome_value", "change", "higher", "p_10y", "p_all", "implied", "hit"]


def update(today, state):
    """today: ISO date; state: dict from build_site with the active supported conditions. Appends new forecasts and entries, resolves matured ones. Returns the three tables."""
    os.makedirs(LEDGER, exist_ok=True); sc = series()
    fc = _read("forecasts.csv", FC_COLS); en = _read("entries.csv", EN_COLS); rs = _read("resolved.csv", RS_COLS)
    have_f = set(fc["id"])
    for scope, (s, unit, hs, win) in sc.items():
        a = len(s) - 1; anchor = str(s.index[a])[:7] if unit == "month" else str(s.index[a])
        for h in hs:
            fid = f"{scope}|{anchor}|{h}"
            if fid in have_f: continue
            p10, n10, pall, nall = base_rate(s, a, h, win)
            fc.loc[len(fc)] = [fid, today, scope, anchor, unit, h, f"{p10:.4f}", n10, f"{pall:.4f}", f"{s.iloc[a]:.2f}"]
    have_e = set(en["id"])
    for scope, acts in state.items():
        if scope not in sc: continue
        s, unit, hs, win = sc[scope]; anchor = str(s.index[-1])[:7] if unit == "month" else str(s.index[-1])
        for a_ in acts:
            eid = f"{scope}|{a_['family']}|{a_['tau']}|{a_['tail']}|{anchor}"
            open_same = en[(en["scope"] == scope) & (en["family"] == a_["family"]) & (en["tau"] == str(a_["tau"])) & (en["tail"] == a_["tail"])]
            if eid in have_e: continue
            # an entry stays open until its longest horizon has resolved; do not re-log the same condition while open
            if len(open_same) and not _resolved_all(open_same.iloc[-1], rs, sc): continue
            en.loc[len(en)] = [eid, today, scope, a_["family"], a_["tau"], a_["tail"], a_["implied"], anchor, unit, f"{s.iloc[-1]:.2f}"]
    done = set(zip(rs["kind"], rs["id"], rs["horizon"]))
    for kind, tab in (("forecast", fc), ("entry", en)):
        for r in tab.itertuples():
            scope = r.scope
            if scope not in sc: continue
            s, unit, hs, win = sc[scope]
            hlist = [int(r.horizon)] if kind == "forecast" else list(hs)
            for h in hlist:
                if (kind, r.id, str(h)) in done: continue
                pos = _locate(s, r.anchor, unit)
                if pos is None or pos + h >= len(s): continue
                v0, v1 = float(s.iloc[pos]), float(s.iloc[pos + h]); ch = np.log(v1 / v0)
                implied = getattr(r, "implied", ""); p10 = getattr(r, "p_10y", ""); pa = getattr(r, "p_all", "")
                rs.loc[len(rs)] = [kind, r.id, scope, r.anchor, h, unit, str(s.index[pos + h])[:7] if unit == "month" else str(s.index[pos + h]), f"{v0:.2f}", f"{v1:.2f}", f"{ch:.5f}", int(v1 > v0), p10 if kind == "forecast" else "", pa if kind == "forecast" else "", implied if kind == "entry" else "", (int((v1 > v0) == (implied == "higher")) if kind == "entry" else "")]
    for name, tab in (("forecasts.csv", fc), ("entries.csv", en), ("resolved.csv", rs)): tab.to_csv(os.path.join(LEDGER, name), index=False)
    return fc, en, rs


def _locate(s, anchor, unit):
    try:
        key = pd.Timestamp(anchor + "-01") if unit == "month" else pd.Period(anchor, freq="Q")
        return int(s.index.get_loc(key))
    except Exception:
        return None


def _resolved_all(entry, rs, sc):
    s, unit, hs, win = sc[entry["scope"]]
    got = set(rs[(rs["kind"] == "entry") & (rs["id"] == entry["id"])]["horizon"]); return all(str(h) in got for h in hs)
