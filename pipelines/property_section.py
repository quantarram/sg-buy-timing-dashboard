"""Property section of the dashboard: returns HTML fragments and chart traces. Used by build_site.py."""
import json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import property_predictors as pr, property_state as ps, property_panel as pp, ura_panel

EXCLUDED = {"fair"}
LABEL = {"momentum": "Price momentum", "rentgrowth": "Rent growth", "rates": "2-year government yield change", "pipeline": "Supply pipeline change", "volume": "Units transacted change", "unsold": "Unsold approved units change",
         "value": "Price-to-rent vs its 5-year mean", "vacancy": "Vacancy rate vs its 5-year mean", "salesratio": "New sales / launches"}
REP = [("momentum", 4), ("rentgrowth", 4), ("rates", 4), ("pipeline", 4), ("volume", 4), ("unsold", 4), ("value", 0), ("vacancy", 0), ("salesratio", 0)]
C = {"nonlanded": "#C9A84C", "landed": "#E08FB8", "nl_ccr": "#7FB5E0", "nl_rcr": "#4DB87A", "nl_ocr": "#B07FE0"}


def supported(sup, fam):
    if fam in EXCLUDED or fam not in sup.index: return False
    r = sup.loc[fam]
    return bool(r["lift_all"] >= 1.4 and r["lift_2017"] >= 1.4 and r["entries_all"] >= 100)


def tr(x, y, name, color, width=2, dash=None):
    d = dict(x=[str(i) if not hasattr(i, "to_timestamp") else str(i.to_timestamp())[:10] for i in x], y=[None if pd.isna(v) else round(float(v), 2) for v in y], name=name, type="scatter", mode="lines", line=dict(color=color, width=width))
    if dash: d["line"]["dash"] = dash
    return d


def pill(txt, tone): return f'<span class="pill tone-{tone}">{txt}</span>'


def build(sup):
    P, R, T, N, S, gov = pr.load()
    rows, ex = ps.indicators(P, R, T, N, S); base = ps.base_rates(P); dd = {t: ps.drawdowns(P[t]) for t in ("nonlanded", "landed")}
    n_active = 0; out = {}
    # ---- cards
    cards = []
    for r in rows:
        yo = r["yoy"] * 100; cls = "down" if yo < 0 else "up"
        cards.append(f'''<section class="card"><div class="cardhead"><h3>{r["name"]}</h3>{pill("WAIT &amp; WATCH", "neutral")}</div>
<div class="big">{r["index"]:.1f}</div><div class="sub">price index (2009 Q1 = 100), {ex["last_q"]}</div>
<dl><dt>Year on year</dt><dd>{yo:+.1f}%</dd><dt>Last quarter</dt><dd>{r["qoq"]*100:+.1f}%</dd><dt>From its peak ({r["peak_q"]})</dt><dd>{r["from_peak"]*100:+.1f}%</dd><dt>Price-to-rent, percentile of history</dt><dd>{r["ptr_pct"]:.0f}</dd></dl></section>''')
    out["PROP_CARDS"] = "".join(cards)
    # ---- state tables for condo (all regions) and landed
    for key, tgt in (("PROP_STATE_CONDO", "nonlanded"), ("PROP_STATE_LANDED", "landed")):
        lp, X, sign = pr.build_X(tgt, P, R, T, N, S, gov); t = ['<table><thead><tr><th>Predictor</th><th>Percentile</th><th>Read</th><th>Past evidence (lift: all years, since 2017)</th></tr></thead><tbody>']
        for fam, tau in REP:
            xs = X[(fam, tau)].dropna(); v = xs.iloc[-1]; pct = float((xs.iloc[:-1] < v).mean() * 100); tail = "low" if pct <= 20 else ("high" if pct >= 80 else "")
            sp = supported(sup, fam); active = sp and bool(tail)
            if active: n_active += 1
            read = pill("active", "warn") if active else (pill("tail, not supported", "note") if tail else pill("normal range", "neutral"))
            ev = f'{sup.loc[fam, "lift_all"]:.2f} ({int(sup.loc[fam, "entries_all"])} entries), {sup.loc[fam, "lift_2017"]:.2f}' if fam in sup.index else "not scored"
            lab = LABEL[fam] + (f" ({tau} quarters)" if tau else "")
            t.append(f'<tr><td>{lab}</td><td class="num">{pct:.0f}</td><td>{read}</td><td>{ev}</td></tr>')
        t.append("</tbody></table>"); out[key] = "".join(t)
    out["PROP_ACTIVE"] = n_active
    # ---- base rates
    b = ['<table><thead><tr><th>Segment</th><th>Window</th><th>Lower after 4q</th><th>Median 4q</th><th>Lower after 8q</th><th>Median 8q</th><th>Worst 4q</th></tr></thead><tbody>']
    for t_, d in base.items():
        for lab in ("since 2004", "last 10 years"):
            a, c = d[lab][4], d[lab][8]
            b.append(f'<tr><td>{ps.NAMES[t_] if lab=="since 2004" else ""}</td><td>{lab}</td><td class="num">{a["lower"]*100:.0f}%</td><td class="num">{a["med"]*100:+.1f}%</td><td class="num">{c["lower"]*100:.0f}%</td><td class="num">{c["med"]*100:+.1f}%</td><td class="num">{a["worst"]*100:+.0f}%</td></tr>')
    b.append("</tbody></table>"); out["PROP_BASE"] = "".join(b)
    d = ['<table><thead><tr><th>Series</th><th>Peak</th><th>Trough</th><th>Fall</th><th>Quarters down</th><th>Quarters to recover</th></tr></thead><tbody>']
    for t_, eps in dd.items():
        for pk, tro, depth, q1, q2 in eps:
            d.append(f'<tr><td>{ps.NAMES[t_]}</td><td>{pk}</td><td>{tro}</td><td class="num">{depth*100:.0f}%</td><td class="num">{q1}</td><td class="num">{q2 if q2 is not None else "not yet"}</td></tr>')
    d.append("</tbody></table>"); out["PROP_DD"] = "".join(d)
    # ---- supply and EC
    E = pp.executive_condos(); e = E.iloc[-1]
    fmt = lambda v: "n/a" if pd.isna(v) else f"{v:,.0f}"
    sup_rows = [("Vacant private homes (share of available)", f'{ex["vacancy"]*100:.1f}% (percentile {ex["vacancy_pct"]:.0f} of history)'), ("Unsold approved units", f'{ex["unsold"]:,.0f} (percentile {ex["unsold_pct"]:.0f})'),
                ("Non-landed supply pipeline", f'{ex["pipeline_nonlanded"]:,.0f} units'), ("Units sold / launched, uncompleted", f'{ex["sold_to_launched"]:.2f}'), ("Private transactions this quarter", f'{ex["txn_total"]:,.0f} ({ex["txn_yoy"]*100:+.0f}% year on year; {ex["new_sale"]:,.0f} new sale, {ex["resale"]:,.0f} resale)')]
    ec_rows = [("EC stock available / vacant", f'{fmt(e["ec_available"])} / {fmt(e["ec_vacant"])} ({e["ec_vacancy_rate"]*100:.1f}% vacant)'), ("EC supply pipeline", f'{fmt(e["ec_pipeline_total"])} units ({fmt(e["ec_under_construction"])} under construction)'),
               ("EC launched and sold (uncompleted, cumulative position)", f'{fmt(e["ec_launched_and_sold"])} sold, {fmt(e["ec_launched_unsold"])} launched but unsold'), ("EC new-sale units sold this quarter", fmt(e["ec_new_sold_uncompleted"]))]
    tab = lambda rows_: '<table><tbody>' + "".join(f'<tr><td>{a}</td><td class="num">{b_}</td></tr>' for a, b_ in rows_) + "</tbody></table>"
    out["PROP_SUPPLY"] = tab(sup_rows); out["PROP_EC"] = tab(ec_rows)
    # ---- charts
    p1 = [tr(P.index, P[t], ps.NAMES[t], C[t], 2 if t in ("nonlanded", "landed") else 1.4) for t in ("nonlanded", "landed", "nl_ccr", "nl_rcr", "nl_ocr")]
    ptr_idx = P.index[P.index >= pd.Period("1990Q1")]
    p2 = [tr(ptr_idx, P.loc[ptr_idx, "nonlanded"], "Non-landed price index", C["nonlanded"]), tr(ptr_idx, R["all_wi"].reindex(ptr_idx), "Rental index (whole island)", "#7FB5E0")]
    tx = T["wi"][["new_sale", "resale", "sub_sale"]]; tx = tx[tx.index >= pd.Period("2004Q1")]
    p3 = [dict(x=[str(i.to_timestamp())[:10] for i in tx.index], y=[float(v) for v in tx[c]], name=nm, type="bar", marker=dict(color=col)) for c, nm, col in (("new_sale", "New sale", "#C9A84C"), ("resale", "Resale", "#7FB5E0"), ("sub_sale", "Sub sale", "#7A8F7A"))]

    # ---- EC and condo prices from URA transactions (needs data/ura/monthly_by_type.csv)
    if ura_panel.available():
        import datetime as dt
        U = ura_panel.load(); lm = ura_panel.latest_full_month(U, dt.date.today()); ly = lm - pd.DateOffset(years=1)
        rows_ = ['<table><thead><tr><th>Median, single-unit sales</th><th>Month</th><th>Units</th><th>Price</th><th>Per sq ft</th><th>Per sq ft, year on year</th></tr></thead><tbody>']
        for nm, s_ in U.items():
            if lm in s_.index and ly in s_.index:
                yo = s_.loc[lm, "psf"] / s_.loc[ly, "psf"] - 1; rows_.append(f'<tr><td>{nm}</td><td>{lm.strftime("%b %Y")}</td><td class="num">{s_.loc[lm, "units"]:,.0f}</td><td class="num">S${s_.loc[lm, "price"]:,.0f}</td><td class="num">S${s_.loc[lm, "psf"]:,.0f}</td><td class="num">{yo*100:+.1f}%</td></tr>')
        rows_.append("</tbody></table>"); out["PROP_EC_PRICES"] = "".join(rows_)
        cols = {"EC new sale": "#C9A84C", "EC resale": "#E8A020", "Condo new sale": "#7FB5E0", "Condo resale": "#4DB87A"}
        pe = [tr(U[nm].index, U[nm]["psf"], nm, cols[nm], 1.8, "dot" if "new" in nm else None) for nm in U]
        out["PROP_C4"] = json.dumps(pe)
    else:
        out["PROP_EC_PRICES"] = "<p class='tag'>EC prices need the URA access key (not configured in this build).</p>"; out["PROP_C4"] = "[]"
    allr = sup.loc["ALL"]; fade = [LABEL[f].split(" (")[0].lower() for f in sup.index if f not in ("ALL", "momentum") and sup.loc[f, "entries_pre2017"] >= 100 and sup.loc[f, "lift_pre2017"] >= 1.4 and sup.loc[f, "lift_2017"] < 1.0]
    mom = sup.loc["momentum"]
    out["PROP_EVIDENCE"] = (f'<div class="block"><ul><li><b>Nothing beats the base rate in the latest decade.</b> Across {int(allr["cond_years"]):,} admitted condition-years the out-of-sample lift is {allr["lift_all"]:.2f} overall and {allr["lift_2017"]:.2f} since 2017 (1.0 is no better than the base rate).</li>'
        f'<li><b>Momentum worked in one cycle.</b> Price momentum scored a lift of {mom["lift_pre2017"]:.1f} up to 2016 (largely the 2008 to 2010 swings) and {mom["lift_2017"]:.1f} since 2017.' + (f' The same fade shows in: {", ".join(fade)}.' if fade else "") + '</li>'
        '<li><b>Why.</b> Only about six real price cycles in the data, and policy measures from 2011 on may have changed how the market behaves; neither is tested here.</li>'
        '<li><b>So the page shows risk, not a call:</b> the full drawdown history and the base rates over both windows.</li></ul></div>')
    out["PROP_C1"] = json.dumps(p1); out["PROP_C2"] = json.dumps(p2); out["PROP_C3"] = json.dumps(p3); out["PROP_Q"] = ex["last_q"]
    return out
