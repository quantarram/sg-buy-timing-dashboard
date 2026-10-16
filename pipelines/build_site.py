"""Build docs/index.html: the public Singapore buy-timing dashboard (COE first), from the committed data and the walk-forward summary.
python pipelines/build_site.py   (run research/coe_cpe_walkforward.py first so research/coe_walkforward_summary.csv is current)"""
import datetime as dt, json, os, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import panel
from sgtiming.predictors import build_X, fair_resid

Q = panel.quota_panel(); F = panel.flows(); R = panel.rates(); idx = Q["A"].index
ex = pd.read_csv(os.path.join(ROOT, "data", "coe_results.csv"))
for c in ["quota", "bids_success", "bids_received", "premium"]: ex[c] = pd.to_numeric(ex[c], errors="coerce")
ex["t"] = pd.to_datetime(ex["month"] + "-01") + pd.to_timedelta((ex["bidding_no"] - 1) * 14, unit="D")
WF = pd.read_csv(os.path.join(ROOT, "research", "coe_walkforward_summary.csv")).set_index("group")
CAT = {"A": "Category A", "B": "Category B"}
SGT = dt.timezone(dt.timedelta(hours=8)); now = dt.datetime.now(SGT)
fmt = lambda v: f"{v:,.0f}"

# ---- latest rounds ------------------------------------------------------------------------------------------------------------------------------
cards = {}
for c, name in CAT.items():
    s = ex[ex["vehicle_class"] == name].sort_values("t").reset_index(drop=True); last, prev = s.iloc[-1], s.iloc[-2]
    m = Q[c]; mp = m["premium"].dropna()
    cards[c] = dict(last=last["premium"], prev=prev["premium"], chg=last["premium"] / prev["premium"] - 1, month=last["month"], rnd=int(last["bidding_no"]),
                    quota=int(last["quota"]), bids=(None if pd.isna(last["bids_received"]) else int(last["bids_received"])), pqp=m["pqp"].dropna().iloc[-1], pqp_month=m["pqp"].dropna().index[-1].strftime("%b %Y"),
                    hi12=s["premium"].iloc[-26:].max(), lo12=s["premium"].iloc[-26:].min(), ath=s["premium"].max(), ath_date=s.loc[s["premium"].idxmax(), "t"].strftime("%b %Y"))

# ---- registered predictors, current state ------------------------------------------------------------------------------------------------------
EVID = {"quota": ("Quota change", "a cut leads to a higher premium; increases do not lead to lower", WF.loc["fam=quota", "lift"], int(WF.loc["fam=quota", "entries"])),
        "spread": ("B/A spread", "A and B premiums move back toward each other", WF.loc["fam=spread", "lift"], int(WF.loc["fam=spread", "entries"])),
        "bids": ("Bids per quota", "heavier bidding leads to a higher premium", WF.loc["fam=bids", "lift"], int(WF.loc["fam=bids", "entries"])),
        "value": ("Premium vs its 12-month mean", "reversion toward the mean", None, 0),
        "momentum": ("Premium momentum", "continuation", WF.loc["fam=momentum", "lift"], int(WF.loc["fam=momentum", "entries"])),
        "supplycycle": ("Supply cycle (de-registrations 6 to 18 months ago)", "falling supply leads to a higher premium", WF.loc["fam=supplycycle", "lift"], int(WF.loc["fam=supplycycle", "entries"]))}
state = {}; active = {}
for c in CAT:
    lp, lq, X, sign = build_X(c, Q, F, R); rows = []
    for fam, tau in [("quota", 6), ("quota", 12), ("bids", 6), ("spread", 0), ("value", 0), ("momentum", 6), ("supplycycle", 12)]:
        xs = X[(fam, tau)]; v = xs.iloc[-1]; hist = xs.iloc[:-1].dropna(); pct = float((hist < v).mean() * 100) if pd.notna(v) else np.nan
        tail = "low" if pct <= 20 else ("high" if pct >= 80 else "")
        evid = EVID[fam]; supported = evid[2] is not None and evid[2] >= 1.4 and fam in ("quota", "spread")
        # an admitted condition: quota cut (low tail) for quota; either spread tail
        is_active = bool(supported and tail and (fam != "quota" or tail == "low"))
        implied = ""
        if is_active: implied = "higher" if (sign[fam] > 0) == (tail == "high") else "lower"
        rows.append(dict(fam=fam, tau=tau, value=v, pct=pct, tail=tail, active=is_active, implied=implied, label=evid[0] + (f" ({tau} months)" if tau else ""), mech=evid[1], lift=evid[2], n=evid[3]))
    state[c] = rows; active[c] = [r for r in rows if r["active"]]

# ---- base rates -----------------------------------------------------------------------------------------------------------------------------------
base = {}
for c in CAT:
    lp = np.log(Q[c]["premium"].dropna()); base[c] = {}
    for lab, start in (("last 10 years", pd.Timestamp("2016-10-01")), ("since 2002", lp.index[0])):
        base[c][lab] = {h: dict(lower=float(np.mean((lp.shift(-h) - lp)[lp.index >= start].dropna() < 0)), up5=float(np.mean((lp.shift(-h) - lp)[lp.index >= start].dropna() > 0.05)), dn5=float(np.mean((lp.shift(-h) - lp)[lp.index >= start].dropna() < -0.05)), med=float(np.median((lp.shift(-h) - lp)[lp.index >= start].dropna()))) for h in (3, 6, 12)}

# ---- supply cycle ----------------------------------------------------------------------------------------------------------------------------------
nr = F["newreg_A"] + F["newreg_B"]; dr = F["dereg_A"] + F["dereg_B"]; sched = nr.copy(); sched.index = sched.index + pd.DateOffset(months=120)
sched6 = sched.rolling(6).mean(); dr6 = dr.rolling(6).mean()
sched12_now = float(sched.rolling(12).mean()["2026-08-01"]); sched12_1y = float(sched.rolling(12).mean()["2027-08-01"]); dr12_now = float(dr.rolling(12).mean().iloc[-1])

# ---- charts ----------------------------------------------------------------------------------------------------------------------------------------
def tr(x, y, name, color, dash=None, width=2):
    d = dict(x=[str(i)[:10] for i in x], y=[None if pd.isna(v) else round(float(v), 2) for v in y], name=name, type="scatter", mode="lines", line=dict(color=color, width=width));
    if dash: d["line"]["dash"] = dash
    return d
C_A, C_B, C_G, C_O = "#2563eb", "#dc2626", "#16a34a", "#d97706"
long_traces = [tr(Q[c].index, Q[c]["premium"] / 1000, CAT[c], col) for c, col in (("A", C_A), ("B", C_B))]
recent = []
for c, col in (("A", C_A), ("B", C_B)):
    s = ex[(ex["vehicle_class"] == CAT[c]) & (ex["t"] >= ex["t"].max() - pd.Timedelta(days=3 * 365))].sort_values("t"); recent.append(tr(s["t"], s["premium"] / 1000, CAT[c], col))
cycle_traces = [tr(dr6.index, dr6, "De-registrations A+B (6-month mean)", C_O), tr(sched6.index[sched6.index <= "2030-01-01"], sched6[sched6.index <= "2030-01-01"], "Scheduled expiries (registrations 10 years earlier)", C_G, "dot"), tr(nr.index, nr.rolling(6).mean(), "New registrations A+B (6-month mean)", "#94a3b8", None, 1)]

# ---- html -------------------------------------------------------------------------------------------------------------------------------------------
def pill(txt, kind): return f'<span class="pill {kind}">{txt}</span>'
def card(c):
    d = cards[c]; chg = d["chg"] * 100; sign = "up" if chg > 0 else "down"
    act = active[c]; st = pill(f"{len(act)} condition{'s' if len(act)!=1 else ''} active", "warn") if act else pill("no condition active", "calm")
    bids = f"{d['bids']:,} bids for {d['quota']:,} quota" if d["bids"] else f"quota {d['quota']:,}"
    return f'''<section class="card"><div class="cardhead"><h3>{CAT[c]}</h3>{st}</div>
<div class="big">S${fmt(d["last"])}</div><div class="sub {sign}">{chg:+.1f}% vs the previous round (S${fmt(d["prev"])}) &middot; round {d["rnd"]}, {d["month"]}</div>
<dl><dt>This round</dt><dd>{bids}</dd><dt>Prevailing premium ({d["pqp_month"]})</dt><dd>S${fmt(d["pqp"])}</dd><dt>Last 12 months</dt><dd>S${fmt(d["lo12"])} to S${fmt(d["hi12"])}</dd><dt>Highest since 2010</dt><dd>S${fmt(d["ath"])} ({d["ath_date"]})</dd></dl></section>'''
def state_table(c):
    out = ['<table><thead><tr><th>Predictor</th><th>Percentile</th><th>Read</th><th>Past evidence</th></tr></thead><tbody>']
    for r in state[c]:
        read = pill(f"active: premium {r['implied']}", "warn") if r["active"] else (pill("tail, no supported effect", "note") if r["tail"] else pill("normal range", "calm"))
        ev = (f"lift {r['lift']:.2f} on {r['n']:,} entries" + (" (too few to rely on)" if r["n"] < 100 else "")) if r["lift"] is not None else "not scored on its own"
        out.append(f'<tr><td>{r["label"]}</td><td class="num">{r["pct"]:.0f}</td><td>{read}</td><td>{ev}</td></tr>')
    out.append("</tbody></table>"); return "".join(out)
def base_table():
    rows = ['<table><thead><tr><th></th><th colspan="3">Category A</th><th colspan="3">Category B</th></tr><tr><th>Window</th><th>Lower</th><th>Up &gt;5%</th><th>Median</th><th>Lower</th><th>Up &gt;5%</th><th>Median</th></tr></thead><tbody>']
    for lab in ("last 10 years", "since 2002"):
        for h in (3, 6, 12):
            a, b = base["A"][lab][h], base["B"][lab][h]
            rows.append(f'<tr><td>{h} months ahead, {lab}</td>' + "".join(f'<td class="num">{x["lower"]*100:.0f}%</td><td class="num">{x["up5"]*100:.0f}%</td><td class="num">{x["med"]*100:+.1f}%</td>' for x in (a, b)) + "</tr>")
    rows.append("</tbody></table>"); return "".join(rows)
n_act = sum(len(v) for v in active.values())
headline = ("No condition from the registered set is active. The premium sits near record highs, so the useful reading is the base rates below, not a call." if not n_act else f"{n_act} registered condition(s) active; see the table for what each implies and how much past evidence stands behind it.")
asof = f'Latest bidding exercise: round {cards["A"]["rnd"]} of {cards["A"]["month"]} &middot; monthly series to {Q["A"].index[-1].strftime("%b %Y")} &middot; built {now.strftime("%d %b %Y %H:%M")} SGT'
quota_cut_12 = WF.loc["ALL admitted", "lift"]
html = open(os.path.join(ROOT, "pipelines", "template.html"), encoding="utf-8").read()
rep = {"{{ASOF}}": asof, "{{HEADLINE}}": headline, "{{CARD_A}}": card("A"), "{{CARD_B}}": card("B"), "{{STATE_A}}": state_table("A"), "{{STATE_B}}": state_table("B"), "{{BASE}}": base_table(),
       "{{LONG}}": json.dumps(long_traces), "{{RECENT}}": json.dumps(recent), "{{CYCLE}}": json.dumps(cycle_traces),
       "{{SCHED_NOW}}": f"{sched12_now:,.0f}", "{{SCHED_1Y}}": f"{sched12_1y:,.0f}", "{{DEREG_NOW}}": f"{dr12_now:,.0f}", "{{OVERALL_LIFT}}": f"{quota_cut_12:.2f}",
       "{{ENTRIES}}": f'{int(WF.loc["ALL admitted", "entries"]):,}'}
for k, v in rep.items(): html = html.replace(k, v)
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True); open(os.path.join(ROOT, "docs", "index.html"), "w", encoding="utf-8").write(html)
open(os.path.join(ROOT, "docs", ".nojekyll"), "w").close()
print("wrote docs/index.html;", "active:", {c: [(r["fam"], r["tau"], r["implied"]) for r in a] for c, a in active.items()})
