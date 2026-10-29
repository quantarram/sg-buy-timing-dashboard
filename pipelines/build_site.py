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
for c in ["quota", "bids_success", "bids_received", "premium"]: ex[c] = pd.to_numeric(ex[c].astype(str).str.replace(",", "", regex=False), errors="coerce")
ex["t"] = pd.to_datetime(ex["month"] + "-01") + pd.to_timedelta((ex["bidding_no"] - 1) * 14, unit="D")
WF = pd.read_csv(os.path.join(ROOT, "research", "coe_walkforward_summary.csv")).set_index("group")
SUP = pd.read_csv(os.path.join(ROOT, "research", "coe_family_support.csv")).set_index("family")
sys.path.insert(0, os.path.join(ROOT, "pipelines"))
import property_section
def is_supported(fam):
    """A family counts as supported when its walk-forward lift is at least 1.4 over all test years and since 2017, on at least 100 entries (the quota-implied level is excluded: specification problem)."""
    return property_section.supported(SUP, fam)
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
L = lambda f: (float(SUP.loc[f, "lift_all"]), int(SUP.loc[f, "entries_all"]), float(SUP.loc[f, "lift_2017"]))
EVID = {"quota": ("Quota change", "a cut leads to a higher premium; increases do not lead to lower", *L("quota")),
        "spread": ("B/A spread", "A and B premiums move back toward each other", *L("spread")),
        "bids": ("Bids per quota", "heavier bidding leads to a higher premium", *L("bids")),
        "value": ("Premium vs its 12-month mean", "reversion toward the mean", None, 0, None),
        "momentum": ("Premium momentum", "continuation", *L("momentum")),
        "supplycycle": ("Supply cycle (de-registrations 6 to 18 months ago)", "falling supply leads to a higher premium", *L("supplycycle"))}
state = {}; active = {}
for c in CAT:
    lp, lq, X, sign = build_X(c, Q, F, R); rows = []
    for fam, tau in [("quota", 6), ("quota", 12), ("bids", 6), ("spread", 0), ("value", 0), ("momentum", 6), ("supplycycle", 12)]:
        xs = X[(fam, tau)]; v = xs.iloc[-1]; hist = xs.iloc[:-1].dropna(); pct = float((hist < v).mean() * 100) if pd.notna(v) else np.nan
        tail = "low" if pct <= 20 else ("high" if pct >= 80 else "")
        evid = EVID[fam]; supported = is_supported(fam)
        # an admitted condition: quota cut (low tail) for quota; either spread tail
        is_active = bool(supported and tail and (fam != "quota" or tail == "low"))
        implied = ""
        if is_active: implied = "higher" if (sign[fam] > 0) == (tail == "high") else "lower"
        rows.append(dict(fam=fam, tau=tau, value=v, pct=pct, tail=tail, active=is_active, implied=implied, label=evid[0] + (f" ({tau} months)" if tau else ""), mech=evid[1], lift=evid[2], n=evid[3], lift17=evid[4]))
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
C_A, C_B, C_G, C_O = "#C9A84C", "#7FB5E0", "#4DB87A", "#E8A020"
long_traces = [tr(Q[c].index, Q[c]["premium"] / 1000, CAT[c], col) for c, col in (("A", C_A), ("B", C_B))]
recent = []
for c, col in (("A", C_A), ("B", C_B)):
    s = ex[(ex["vehicle_class"] == CAT[c]) & (ex["t"] >= ex["t"].max() - pd.Timedelta(days=3 * 365))].sort_values("t"); recent.append(tr(s["t"], s["premium"] / 1000, CAT[c], col))
_w = lambda s_: s_[(s_.index >= "2002-01-01") & (s_.index <= "2030-01-01")]
cycle_traces = [tr(_w(dr6).index, _w(dr6), "De-registrations A+B (6-month mean)", C_O), tr(_w(sched6).index, _w(sched6), "Scheduled expiries (registrations 10 years earlier)", C_G, "dot"), tr(_w(nr.rolling(6).mean()).index, _w(nr.rolling(6).mean()), "New registrations A+B (6-month mean)", "#7A8F7A", None, 1)]

# ---- html -------------------------------------------------------------------------------------------------------------------------------------------
TONE = {"neutral": "tone-neutral", "warn": "tone-warn", "good": "tone-good", "note": "tone-note"}
def pill(txt, kind): return f'<span class="pill {TONE[kind]}">{txt}</span>'
def verdict(c):
    """Graded verdict from the registered conditions: WAIT & WATCH when none is active (the default)."""
    act = active[c]
    if not act: return "WAIT &amp; WATCH", "neutral"
    imp = {r["implied"] for r in act}
    if imp == {"higher"}: return "RISING PRESSURE", "warn"
    if imp == {"lower"}: return "EASING PRESSURE", "good"
    return "MIXED SIGNALS", "warn"
def card(c):
    d = cards[c]; chg = d["chg"] * 100; sign = "up" if chg > 0 else "down"
    vt, vk = verdict(c); st = pill(vt, vk)
    bids = f"{d['bids']:,} bids for {d['quota']:,} quota" if d["bids"] else f"quota {d['quota']:,}"
    return f'''<section class="card"><div class="cardhead"><h3>{CAT[c]}</h3>{st}</div>
<div class="big">S${fmt(d["last"])}</div><div class="sub {sign}">{chg:+.1f}% vs the previous round (S${fmt(d["prev"])}) &middot; round {d["rnd"]}, {d["month"]}</div>
<dl><dt>This round</dt><dd>{bids}</dd><dt>Prevailing premium ({d["pqp_month"]})</dt><dd>S${fmt(d["pqp"])}</dd><dt>Last 12 months</dt><dd>S${fmt(d["lo12"])} to S${fmt(d["hi12"])}</dd><dt>Highest since 2010</dt><dd>S${fmt(d["ath"])} ({d["ath_date"]})</dd></dl></section>'''
def state_table(c):
    out = ['<table><thead><tr><th>Predictor</th><th>Percentile</th><th>Read</th><th>Past evidence</th></tr></thead><tbody>']
    for r in state[c]:
        read = pill(f"active: premium {r['implied']}", "warn") if r["active"] else (pill("tail, no supported effect", "note") if r["tail"] else pill("normal range", "neutral"))
        ev = (f"lift {r['lift']:.2f} on {r['n']:,} entries; since 2017: {r['lift17']:.2f}" + (" (too few to rely on)" if r["n"] < 100 else "")) if r["lift"] is not None and r["lift17"] == r["lift17"] else ("not scored on its own" if r["lift"] is None else f"lift {r['lift']:.2f} on {r['n']:,} entries")
        out.append(f'<tr><td>{r["label"]}</td><td class="num">{r["pct"]:.0f}</td><td>{read}</td><td>{ev}</td></tr>')
    out.append("</tbody></table>"); return "".join(out)
def base_table():
    rows = ['<table><thead><tr><th></th><th colspan="3">Category A</th><th colspan="3">Category B</th></tr><tr><th>Window</th><th>Lower</th><th>Up &gt;5%</th><th>Median</th><th>Lower</th><th>Up &gt;5%</th><th>Median</th></tr></thead><tbody>']
    for lab in ("last 10 years", "since 2002"):
        for h in (3, 6, 12):
            a, b = base["A"][lab][h], base["B"][lab][h]
            rows.append(f'<tr><td>{h} months ahead, {lab}</td>' + "".join(f'<td class="num">{x["lower"]*100:.0f}%</td><td class="num">{x["up5"]*100:.0f}%</td><td class="num">{x["med"]*100:+.1f}%</td>' for x in (a, b)) + "</tr>")
    rows.append("</tbody></table>"); return "".join(rows)
PROP = property_section.build(pd.read_csv(os.path.join(ROOT, 'research', 'property_family_support.csv')).set_index('family'))
n_act = sum(len(v) for v in active.values()) + PROP['PROP_ACTIVE']; VA, VB = verdict("A"), verdict("B")
VP = ("WAIT &amp; WATCH", "neutral") if not PROP['PROP_ACTIVE'] else ("CONDITION ACTIVE", "warn")
if not n_act:
    headline = ("<b>WAIT &amp; WATCH.</b> No registered condition is active for cars or for property, so timing carries no measured edge right now. COE premiums and property indices are near record highs: read the base rates, the supply cycle and the drawdown history below."
                "<div class='sub2'>This is not a recommendation to delay a purchase you need. A verdict other than wait and watch appears only when a condition with out-of-sample support is in its tail.</div>")
else:
    headline = (f"<b>{VA[0]} (A) &middot; {VB[0]} (B).</b> {n_act} registered condition(s) active; the table below shows what each implies and how much past evidence stands behind it."
                "<div class='sub2'>Each verdict is a statement about conditions and base rates, not a recommendation.</div>")
badges = "".join(f'<div class="vbadge {TONE[v[1]]}"><span class="vl">Category {c}</span><span class="vt">{v[0]}</span></div>' for c, v in (("A", VA), ("B", VB)))
badges += f'<div class="vbadge {TONE[VP[1]]}"><span class="vl">Property</span><span class="vt">{VP[0]}</span></div>'
legend = "".join(f'<div>{pill(t, k)}</div><div>{d}</div>' for t, k, d in (
    ("WAIT &amp; WATCH", "neutral", "No registered condition with out-of-sample support is in its tail. No measured timing edge; the base rates apply."),
    ("RISING PRESSURE", "warn", "A supported condition (today: a quota cut) is active and past data say the premium was more often in its top moves over the following 6 to 12 months."),
    ("EASING PRESSURE", "good", "A supported condition points to a lower premium (none is supported at present, so this tier is unused)."),
    ("MIXED SIGNALS", "warn", "Active conditions point in opposite directions.")))
asof = f'Latest bidding exercise: round {cards["A"]["rnd"]} of {cards["A"]["month"]} &middot; monthly series to {Q["A"].index[-1].strftime("%b %Y")} &middot; built {now.strftime("%d %b %Y %H:%M")} SGT'
quota_cut_12 = WF.loc["ALL admitted", "lift"]
_sub = pd.read_csv(os.path.join(ROOT, "research", "coe_robustness_subperiods.csv")); _g = lambda p_: _sub[(_sub.period == p_) & (_sub.tf == 6)].iloc[0]
_thr = pd.read_csv(os.path.join(ROOT, 'research', 'coe_robustness_thresholds.csv')); _m = _thr[(_thr.q == 0.2) & (_thr.yq == 0.2)].set_index('tf')
QUOTATXT = (f"After a quota cut the premium was in its top 20% of moves {_m.loc[3,'cpe']*100:.0f}% of the time three months later ({_m.loc[3,'base']*100:.0f}% base), {_m.loc[6,'cpe']*100:.0f}% after six ({_m.loc[6,'base']*100:.0f}%) and {_m.loc[12,'cpe']*100:.0f}% after twelve ({_m.loc[12,'base']*100:.0f}%), with thresholds from past data only.")
POST2022 = (f"The effect is strong through 2021 (six-month lift {_g('2010-2016').lift:.1f} in 2010 to 2016 and {_g('2017-2021').lift:.1f} in 2017 to 2021) and not detected from 2022 (lift {_g('2022-2026').lift:.1f} on {int(_g('2022-2026').entries)} entries): the quota formula changed in 2022 and 2023, and quota cuts have been rare since.")
# ---- ledger state and track record --------------------------------------------------------------------------------------------------------------
import track_section
os.makedirs(os.path.join(ROOT, "data", "ledger"), exist_ok=True)
state_out = {"COE A": [dict(family=r["fam"], tau=r["tau"], tail=r["tail"], implied=r["implied"]) for r in active["A"]], "COE B": [dict(family=r["fam"], tau=r["tau"], tail=r["tail"], implied=r["implied"]) for r in active["B"]]}
for a_ in PROP["PROP_ACTIVE_LIST"]: state_out.setdefault(a_["scope"], []).append(dict(family=a_["family"], tau=a_["tau"], tail=a_["tail"], implied=a_["implied"]))
json.dump({"built": now.strftime("%Y-%m-%d %H:%M SGT"), "active": state_out}, open(os.path.join(ROOT, "data", "ledger", "today_state.json"), "w"), indent=1)
TRACK = track_section.build()
html = open(os.path.join(ROOT, "pipelines", "template.html"), encoding="utf-8").read()
rep = {"{{ASOF}}": asof, "{{HEADLINE}}": headline, "{{BADGES}}": badges, "{{LEGEND}}": legend, "{{CARD_A}}": card("A"), "{{CARD_B}}": card("B"), "{{STATE_A}}": state_table("A"), "{{STATE_B}}": state_table("B"), "{{BASE}}": base_table(),
       "{{LONG}}": json.dumps(long_traces), "{{RECENT}}": json.dumps(recent), "{{CYCLE}}": json.dumps(cycle_traces),
       "{{SCHED_NOW}}": f"{sched12_now:,.0f}", "{{SCHED_1Y}}": f"{sched12_1y:,.0f}", "{{DEREG_NOW}}": f"{dr12_now:,.0f}", "{{OVERALL_LIFT}}": f"{quota_cut_12:.2f}", "{{POST2022}}": POST2022, "{{QUOTATXT}}": QUOTATXT,
       "{{ENTRIES}}": f'{int(WF.loc["ALL admitted", "entries"]):,}'}
for k_, v_ in PROP.items(): rep["{{" + k_ + "}}"] = str(v_)
for k_, v_ in TRACK.items(): rep["{{" + k_ + "}}"] = str(v_)
for k, v in rep.items(): html = html.replace(k, v)
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True); open(os.path.join(ROOT, "docs", "index.html"), "w", encoding="utf-8").write(html)
open(os.path.join(ROOT, "docs", ".nojekyll"), "w").close()
print("wrote docs/index.html;", "active:", {c: [(r["fam"], r["tau"], r["implied"]) for r in a] for c, a in active.items()})
