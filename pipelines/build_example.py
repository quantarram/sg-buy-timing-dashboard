"""Worked example page: timing the sale of a five-room HDB flat on floors 10 to 15 at BLK 184 Jelebu Rd (Bukit Panjang), from public HDB resale data.
Writes docs/example-184-jelebu.html (a dated snapshot, not part of the daily build).  python pipelines/build_example.py
Needs research/hdb_rpi_cpe_walkforward.py to have been run (research/hdb_rpi_family_support.csv and hdb_rpi_state.json)."""
import datetime as dt, json, os, re, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import hdb, property_panel as pp

BLOCK, STREET, TOWN = "184", "JELEBU RD", "BUKIT PANJANG"
GOLD, BLUE, GREEN, PINK, AMBER, GREY = "#C9A84C", "#7FB5E0", "#4DB87A", "#E08FB8", "#E8A020", "#7A8F7A"
d = hdb.tidy(hdb.fetch_all()); d["dt"] = pd.to_datetime(d["month"] + "-01"); d["year"] = d["dt"].dt.year
d["age"] = d["dt"].dt.year + (d["dt"].dt.month - 1) / 12 - d["lease_commence_date"]; d["psf"] = d["resale_price"] / (d["floor_area_sqm"] * 10.7639)
last_full = (d["dt"].max() - pd.offsets.MonthBegin(1)) if d["dt"].max().month == dt.date.today().month and d["dt"].max().year == dt.date.today().year else d["dt"].max()
bp = d[d["town"] == TOWN].copy(); bp["is_blk"] = (bp["block"] == BLOCK) & (bp["street_name"] == STREET)
SEG = lambda x: x[(x["flat_type"] == "5 ROOM") & (x["storey_mid"].between(11, 14))]          # storey ranges 10-12 and 13-15
seg = SEG(bp); blk_all5 = bp[bp["is_blk"] & (bp["flat_type"] == "5 ROOM")].sort_values("dt"); blk_seg = seg[seg["is_blk"]].sort_values("dt")
peers = seg[(~seg["is_blk"]) & (seg["lease_commence_date"].between(2000, 2006))]
lease = int(bp[bp["is_blk"]]["lease_commence_date"].mode().iloc[0])

# ---- hedonic indices ----------------------------------------------------------------------------------------------------------------------------
def design(g, town_fe=False, block=False):
    X = pd.DataFrame({"const": 1.0, "larea": np.log(g["floor_area_sqm"]), "storey": g["storey_mid"].astype(float), "age": g["age"], "age2": g["age"] ** 2}, index=g.index)
    parts = [X, pd.get_dummies(g["flat_type"], prefix="ft", drop_first=True).astype(np.float32)]
    if town_fe: parts.append(pd.get_dummies(g["town"], prefix="t", drop_first=True).astype(np.float32))
    parts.append(pd.get_dummies(g["month"], prefix="m", drop_first=True).astype(np.float32))
    if block: parts.append(g["is_blk"].astype(float).rename("b184"))
    return pd.concat(parts, axis=1).astype(np.float32)


def month_index(g, **kw):
    X = design(g, **kw); b = pd.Series(np.linalg.lstsq(X.values, np.log(g["resale_price"]).values.astype(np.float32), rcond=None)[0], index=X.columns); months = sorted(g["month"].unique())
    s = pd.Series({m: (0.0 if m == months[0] else b[f"m_{m}"]) for m in months}); s.index = pd.to_datetime([m + "-01" for m in s.index]); return s, b


bp_idx, b_all = month_index(bp.assign(is_blk=bp["is_blk"]), block=True); bp_level = 100 * np.exp(bp_idx); block_prem = float(np.exp(b_all["b184"]) - 1)
full = bp_level[bp_level.index <= last_full]; peak_m = full.idxmax(); now_v = float(full.iloc[-1])
# September by town and pooled
def sep_stats(s):
    ch = s.diff().dropna() * 100; ch = ch[ch.index <= last_full]; sep = ch[ch.index.month == 9]; oth = ch[ch.index.month != 9]
    t = sep.mean() / (sep.std() / np.sqrt(len(sep))); return dict(mean=float(sep.mean()), other=float(oth.mean()), pos=int((sep > 0).sum()), n=int(len(sep)), t=float(t), by_year={str(i.year): round(float(v), 2) for i, v in sep.items()})
sep = {"Bukit Panjang": sep_stats(bp_idx)}
for t in ("YISHUN", "TAMPINES", "BEDOK", "JURONG WEST", "SENGKANG", "WOODLANDS", "PUNGGOL"):
    s_, _ = month_index(d[d["town"] == t].assign(is_blk=False)); sep[t.title()] = sep_stats(s_)
s_all, _ = month_index(d.assign(is_blk=False), town_fe=True); sep["All towns pooled"] = sep_stats(s_all)
# five-room model range
s5 = bp[bp["flat_type"] == "5 ROOM"].copy(); X5 = pd.DataFrame({"const": 1.0, "larea": np.log(s5["floor_area_sqm"]), "storey": s5["storey_mid"].astype(float), "age": s5["age"], "age2": s5["age"] ** 2, "b": s5["is_blk"].astype(float)}, index=s5.index)
X5 = pd.concat([X5, pd.get_dummies(s5["month"], prefix="m", drop_first=True).astype(float)], axis=1); y5 = np.log(s5["resale_price"]); beta5 = pd.Series(np.linalg.lstsq(X5.values, y5.values, rcond=None)[0], index=X5.columns)
res5 = pd.Series(y5.values - X5.values @ beta5.values, index=s5.index); sd_blk = float(res5[s5["is_blk"]].std()); block_prem5 = float(np.exp(beta5["b"]) - 1)
mk = last_full.strftime("%Y-%m"); x = pd.Series(0.0, index=X5.columns); x["const"] = 1; x["larea"] = np.log(112); x["storey"] = 12; ag = last_full.year + (last_full.month - 1) / 12 - lease; x["age"] = ag; x["age2"] = ag ** 2; x["b"] = 1; x[f"m_{mk}"] = 1
mu = float(np.exp(x.values @ beta5.values)); lo, hi = mu * np.exp(-sd_blk), mu * np.exp(sd_blk)
# peers by year
yr_blk = blk_seg.groupby("year")["resale_price"].median(); yr_peer = peers.groupby("year")["resale_price"].median(); yr_town = seg.groupby("year")["resale_price"].median()
prem_peer = {int(y): float(yr_blk[y] / yr_peer[y] - 1) for y in yr_blk.index if y in yr_peer.index}
# ---- HDB index state from the repo walk-forward ----------------------------------------------------------------------------------------------------
st = json.load(open(os.path.join(ROOT, "research", "hdb_rpi_state.json"))); fam = pd.read_csv(os.path.join(ROOT, "research", "hdb_rpi_family_support.csv")).set_index("family"); hdb_rpi = pp.hdb_rpi()
LAB = {"momentum": "Own momentum", "privmom": "Private (OCR) momentum", "rates": "2-year yield", "rentgrowth": "Rent growth", "vacancy": "Private vacancy", "volume": "Private volume", "pipeline": "Private pipeline"}

# ---- charts ----------------------------------------------------------------------------------------------------------------------------------------
def line(x_, y_, name, color, width=2, dash=None):
    o = dict(x=[str(i)[:10] for i in x_], y=[None if pd.isna(v) else round(float(v), 2) for v in y_], name=name, type="scatter", mode="lines", line=dict(color=color, width=width))
    if dash: o["line"]["dash"] = dash
    return o
def band(r): return "floors 10 to 15" if 11 <= r <= 14 else ("floors 16 and above" if r > 14 else "floors 9 and below")
C1 = []
for lab, col in (("floors 9 and below", GREY), ("floors 16 and above", BLUE), ("floors 10 to 15", GOLD)):
    g = blk_all5[blk_all5["storey_mid"].map(band) == lab]
    C1.append(dict(x=[str(i)[:10] for i in g["dt"]], y=[float(v) / 1000 for v in g["resale_price"]], text=[f'{r.storey_range}, {r.floor_area_sqm:.0f} sqm' for r in g.itertuples()], name=f"BLK 184 five-room, {lab}", type="scatter", mode="markers", marker=dict(color=col, size=9 if "10 to 15" in lab else 7, opacity=0.95 if "10 to 15" in lab else 0.7), hovertemplate="%{x|%b %Y}<br>S$%{y:,.0f}k<br>%{text}<extra></extra>"))
C1.append(line([pd.Timestamp(f"{y}-07-01") for y in yr_peer.index], yr_peer.values / 1000, "Peers: Bukit Panjang five-room, floors 10 to 15, lease from 2000 to 2006", GREEN, 2, "dot"))
C1.append(line([pd.Timestamp(f"{y}-07-01") for y in yr_town.index], yr_town.values / 1000, "Town: all Bukit Panjang five-room, floors 10 to 15", GREY, 1.5, "dash"))
h = hdb_rpi[hdb_rpi.index >= pd.Period("2012Q1")]; hb = h / h.iloc[0] * 100; bpq = bp_level[bp_level.index <= last_full]
C2 = [line(hb.index.to_timestamp(), hb.values, "HDB Resale Price Index (2012 Q1 = 100)", GOLD), line(bpq.index, bpq.values / bpq.iloc[:3].mean() * 100, "Bukit Panjang, quality adjusted (2012 Q1 = 100)", BLUE, 1.6)]
full_rpi = hdb_rpi; shapes = [dict(type="rect", xref="x", yref="paper", x0=str(pd.Period(a["peak"]).to_timestamp())[:10], x1=str(pd.Period(a["trough"]).to_timestamp())[:10], y0=0, y1=1, fillcolor="rgba(224,85,85,0.15)", line=dict(width=0)) for a in st["drawdowns"]]
C2L = [line(full_rpi.index.to_timestamp(), full_rpi.values, "HDB Resale Price Index (2009 Q1 = 100)", GOLD)]
fl = fam.drop(index="ALL", errors="ignore").sort_values("lift_pre2017", ascending=False)
C3 = [dict(x=[LAB.get(i, i) for i in fl.index], y=[None if pd.isna(v) else round(float(v), 2) for v in fl["lift_pre2017"]], name="test years up to 2016", type="bar", marker=dict(color=GOLD)), dict(x=[LAB.get(i, i) for i in fl.index], y=[None if pd.isna(v) else round(float(v), 2) for v in fl["lift_2017"]], name="2017 onward", type="bar", marker=dict(color=BLUE))]
names = list(sep); C4 = [dict(x=names, y=[round(sep[n]["mean"], 2) for n in names], name="September, average monthly change", type="bar", marker=dict(color=GOLD)), dict(x=names, y=[round(sep[n]["other"], 2) for n in names], name="Other months", type="bar", marker=dict(color=GREY))]

# ---- html pieces ------------------------------------------------------------------------------------------------------------------------------------
fmt = lambda v: f"S${v:,.0f}"; pct = lambda v, p=1: f"{v*100:+.{p}f}%"
rows_blk = "".join(f"<tr><td>{r.month}</td><td>{r.storey_range.title()}</td><td class='num'>{r.floor_area_sqm:.0f}</td><td class='num'>{fmt(r.resale_price)}</td><td class='num'>{fmt(r.psf)}</td></tr>" for r in blk_seg.sort_values("dt", ascending=False).itertuples())
recent5 = blk_all5.sort_values("dt", ascending=False).head(6); rows_recent = "".join(f"<tr><td>{r.month}</td><td>{r.storey_range.title()}</td><td class='num'>{r.floor_area_sqm:.0f}</td><td class='num'>{fmt(r.resale_price)}</td><td class='num'>{fmt(r.psf)}</td></tr>" for r in recent5.itertuples())
def base_rows():
    out = []
    for lab in ("since 1990", "since 2004", "last 10 years"):
        b4, b8 = st["base"][lab]["4"], st["base"][lab]["8"]
        out.append(f"<tr><td>{lab}</td><td class='num'>{b4['lower']*100:.0f}%</td><td class='num'>{b4['med']*100:+.1f}%</td><td class='num'>{b4['p10']*100:+.1f}% to {b4['p90']*100:+.1f}%</td><td class='num'>{b8['lower']*100:.0f}%</td><td class='num'>{b8['med']*100:+.1f}%</td></tr>")
    return "".join(out)
dd_rows = "".join(f"<tr><td>{a['peak']}</td><td>{a['trough']}</td><td class='num'>{a['depth']*100:.0f}%</td><td class='num'>{a['down']}</td><td class='num'>{a['recover'] if a['recover'] is not None else 'not yet'}</td></tr>" for a in st["drawdowns"])
sp_rows = "".join(f"<tr><td>{s['start']} to {s['end']}</td><td class='num'>{s['quarters']}</td><td class='num'>{s['next4_first']*100:+.1f}%</td></tr>" for s in st["flat_spells"])
sep_bp = sep["Bukit Panjang"]; others = [sep[n]["mean"] for n in names if n not in ("Bukit Panjang", "All towns pooled")]
prem_txt = ", ".join(f"{y}: {v*100:+.0f}%" for y, v in prem_peer.items())
allr = fam.loc["ALL"]; mom = fam.loc["momentum"]
text = dict(
 ASOF=f"Snapshot built {dt.datetime.now().strftime('%d %b %Y')} &middot; HDB resales to {d['dt'].max().strftime('%b %Y')} (last full month {last_full.strftime('%b %Y')}) &middot; HDB index to {st['latest']}",
 N_ALL5=str(len(blk_all5)), N_SEG=str(len(blk_seg)), N_PEERS=f"{len(peers):,}", N_PEERBLK=str(peers.groupby(['block', 'street_name']).ngroups), LEASE=str(lease), REMAIN=str(lease + 99 - last_full.year),
 PREM=f"{block_prem*100:+.0f}%", PREM5=f"{block_prem5*100:+.0f}%", MU=fmt(round(mu, -3)), LO=fmt(round(lo, -3)), HI=fmt(round(hi, -3)), SDBLK=f"{sd_blk*100:.1f}%", MONTH=last_full.strftime('%B %Y'),
 BPNOW=f"{now_v:.1f}", BPPEAK=f"{float(full.max()):.1f}", BPPEAKM=peak_m.strftime('%b %Y'), BPVSPEAK=f"{(now_v/float(full.max())-1)*100:+.1f}%", BPYOY=f"{(now_v/float(full.iloc[-13])-1)*100:+.1f}%",
 RPI=f"{st['index']:.1f}", RPIPEAK=f"{st['peak']:.1f}", RPIPEAKQ=st['peak_q'], RPIFROM=f"{st['from_peak']*100:+.1f}%", RPIYOY=f"{st['yoy']*100:+.1f}%",
 ALLLIFT=f"{allr['lift_all']:.2f}", ALL17=f"{allr['lift_2017']:.2f}", CONDYRS=f"{int(allr['cond_years'])}", MOMLIFT=f"{mom['lift_all']:.1f}", MOMN=f"{int(mom['n_all'])}", MOMN17=f"{int(mom['n_2017'])}",
 BASE_ROWS=base_rows(), DD_ROWS=dd_rows, SP_ROWS=sp_rows, ROWS_BLK=rows_blk, ROWS_RECENT=rows_recent, PREM_PEERS=prem_txt,
 FLAT_NEXT4=f"{st['flat_summary']['next4_median']*100:+.1f}%", FLAT_LOWER=f"{st['flat_summary']['next4_lower']*100:.0f}%", FLAT_Q=str(st['flat_summary']['n_quarters']), FLAT_S=str(st['flat_summary']['n_spells']),
 SEP_BP=f"{sep_bp['mean']:+.2f}%", SEP_OTHER=f"{sep_bp['other']:+.2f}%", SEP_POS=f"{sep_bp['pos']} of {sep_bp['n']}", SEP_T=f"{sep_bp['t']:.1f}", SEP_POOL=f"{sep['All towns pooled']['mean']:+.2f}%", SEP_POOL_T=f"{sep['All towns pooled']['t']:.1f}",
 LASTYEAR=str(last_full.year), SEP_OTH_RANGE=f"{min(others):+.2f}% to {max(others):+.2f}%", SEP_LAST=f"{sep_bp['by_year'].get(str(last_full.year), float('nan')):+.1f}%",
 C1=json.dumps(C1), C2=json.dumps(C2), C2L=json.dumps(C2L), C3=json.dumps(C3), C4=json.dumps(C4), SHAPES=json.dumps(shapes))
tmpl = open(os.path.join(ROOT, "pipelines", "example_template.html"), encoding="utf-8").read()
css = re.search(r"<style>(.*?)</style>", open(os.path.join(ROOT, "pipelines", "template.html"), encoding="utf-8").read(), re.S).group(1)
html = tmpl.replace("{{CSS}}", css)
for k, v in text.items(): html = html.replace("{{" + k + "}}", v)
open(os.path.join(ROOT, "docs", "example-184-jelebu.html"), "w", encoding="utf-8").write(html)
left = re.findall(r"\{\{[A-Z0-9_]+\}\}", html); print("placeholders left:", left); print("wrote docs/example-184-jelebu.html")
print(f"block premium (all types) {block_prem*100:+.1f}%, five-room {block_prem5*100:+.1f}%; model {mu:,.0f} ({lo:,.0f} to {hi:,.0f}); segment sales {len(blk_seg)}; peers {len(peers)}; Sept BP {sep_bp['mean']:+.2f}% t {sep_bp['t']:.1f}; pooled {sep['All towns pooled']['mean']:+.2f}% t {sep['All towns pooled']['t']:.1f}")
