"""Track-record section: the live ledger (forward-scored from its start date) and the causal replay of the base-rate forecasts."""
import json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import ledger

UNIT = {"month": "months", "quarter": "quarters"}


def _read(name):
    p = os.path.join(ledger.LEDGER, name); return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()


def build():
    fc, en, rs, retro = _read("forecasts.csv"), _read("entries.csv"), _read("resolved.csv"), _read("retrospective.csv"); out = {}
    nf, ne = len(fc), len(en); rf = rs[rs["kind"] == "forecast"] if len(rs) else rs; re_ = rs[rs["kind"] == "entry"] if len(rs) else rs
    pend = []
    if nf:
        sc = ledger.series()
        for r in fc.itertuples():
            if len(rf) and ((rf["id"] == r.id) & (rf["horizon"] == r.horizon)).any(): continue
            s, unit, hs, win = sc[r.scope]; a = pd.Timestamp(r.anchor + "-01") if unit == "month" else pd.Period(r.anchor, freq="Q"); due = a + pd.DateOffset(months=int(r.horizon)) if unit == "month" else a + int(r.horizon)
            pend.append((due.to_timestamp() if hasattr(due, "to_timestamp") else due, unit))
    first, first_unit = min(pend, key=lambda x: x[0]) if pend else (None, None)
    first_txt = (f"The first live outcomes arrive once the data for {first.strftime('%B %Y')} are published, a few weeks after that month." if first is not None and first_unit == "month" else (f"The first live outcomes arrive from {first.strftime('%B %Y')}." if first is not None else "No outcomes pending."))
    rows = [("Ledger started", ledger.START), ("Base-rate forecasts logged", f"{nf} (scored {len(rf)})"), ("Condition entries logged", f"{ne} (horizons scored {len(re_)})")]
    out["TRACK_STATUS"] = '<table><tbody>' + "".join(f"<tr><td>{a}</td><td class='num'>{b}</td></tr>" for a, b in rows) + "</tbody></table>" + f"<p class='tag' style='margin-top:8px'>{first_txt} Each month (COE) or quarter (property) the dashboard logs what its base rates imply before the outcome is known; every time a supported condition becomes active it is logged as an entry. Scored items appear below.</p>"
    if nf:
        last = fc.sort_values("anchor").groupby(["scope", "horizon"]).tail(1).sort_values(["scope", "horizon"])
        body = "".join(f"<tr><td>{r.scope}</td><td>{r.anchor}</td><td class='num'>{r.horizon} {UNIT.get(r.unit, '')}</td><td class='num'>{float(r.p_10y)*100:.0f}%</td><td class='num'>{float(r.p_all)*100:.0f}%</td></tr>" for r in last.itertuples())
        out["TRACK_NOW"] = f"<div class='tablewrap'><table><thead><tr><th>Series</th><th>Anchor</th><th>Horizon</th><th>Higher: ten-year base rate</th><th>Higher: all history</th></tr></thead><tbody>{body}</tbody></table></div>"
    else: out["TRACK_NOW"] = ""
    # recent resolved
    if len(rs):
        t = rs.tail(10).iloc[::-1]
        body = "".join(f"<tr><td>{r.kind}</td><td>{r.scope}</td><td>{r.anchor}</td><td class='num'>{r.horizon} {UNIT.get(r.unit, '')}</td><td class='num'>{float(r.change)*100:+.1f}%</td><td>{'higher' if int(r.higher) else 'lower'}</td><td>{(f'forecast {float(r.p_10y)*100:.0f}% (ten-year) and {float(r.p_all)*100:.0f}% (all history) higher' if r.kind == 'forecast' else (f'implied {r.implied}, ' + ('hit' if str(r.hit) in ('1', '1.0') else 'miss')))}</td></tr>" for r in t.itertuples())
        out["TRACK_RECENT"] = f"<div class='tablewrap'><table><thead><tr><th>Kind</th><th>Scope</th><th>Anchor</th><th>Horizon</th><th>Change</th><th>Outcome</th><th>Statement</th></tr></thead><tbody>{body}</tbody></table></div>"
    else:
        out["TRACK_RECENT"] = "<p class='tag'>No scored outcomes yet. They will appear here as the horizons pass.</p>"
    # retrospective
    if len(retro):
        body = "".join(f"<tr><td>{r.scope}</td><td class='num'>{r.horizon} {UNIT.get(r.unit, '')}</td><td class='num'>{int(r.n)}</td><td class='num'>{r.share_higher*100:.0f}%</td><td class='num'>{r.brier_10y:.3f}</td><td class='num'>{r.brier_all:.3f}</td><td class='num'>{r.brier_always_higher:.3f}</td><td class='num'>{r.hit_10y*100:.0f}%</td></tr>" for r in retro.itertuples())
        out["TRACK_RETRO"] = f"<div class='tablewrap'><table><thead><tr><th>Series</th><th>Horizon</th><th>Windows scored</th><th>Actually higher</th><th>Brier, ten-year base rate</th><th>Brier, all-history base rate</th><th>Brier, always &ldquo;higher&rdquo;</th><th>Direction right</th></tr></thead><tbody>{body}</tbody></table></div>"
        g = lambda m: retro[m]; coe = retro["scope"].str.startswith("COE")
        out["TRACK_RETRO_NOTE"] = (f"A Brier score of 0.250 is what a coin flip scores; lower is better. The ten-year base rate beat the coin in {int((retro['brier_10y'] < 0.25).sum())} of {len(retro)} series and horizons, the all-history base rate in {int((retro['brier_all'] < 0.25).sum())}. "
            f"For COE the mean score is {retro[coe]['brier_10y'].mean():.3f} (ten-year) and {retro[coe]['brier_all'].mean():.3f} (all history): about a coin flip. For the property series it is {retro[~coe]['brier_10y'].mean():.3f} and {retro[~coe]['brier_all'].mean():.3f}: the long history is the better guide, because a trailing decade over-reacts to the regime just before it.")
    else:
        out["TRACK_RETRO"] = ""; out["TRACK_RETRO_NOTE"] = ""
    # COE walk-forward lift by test year
    p = os.path.join(ROOT, "research", "coe_walkforward_summary.csv")
    if os.path.exists(p):
        s = pd.read_csv(p); y = s[s["group"].str.startswith("year=")].copy(); y["year"] = y["group"].str[5:].astype(int)
        tr = [dict(x=[int(v) for v in y["year"]], y=[round(float(v), 2) for v in y["lift"]], type="bar", name="lift over the base rate", marker=dict(color=["#4DB87A" if v >= 1 else "#E05555" for v in y["lift"]]), text=[f"n={int(n)}" for n in y["entries"]], hovertemplate="%{x}: lift %{y}<br>%{text}<extra></extra>")]
        out["TRACK_C1"] = json.dumps(tr)
    else:
        out["TRACK_C1"] = "[]"
    return out
