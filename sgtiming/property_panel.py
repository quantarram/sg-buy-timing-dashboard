"""Quarterly Singapore property panel from the data.gov.sg series in data/property/ (URA and related), indexed by pandas quarterly Period.

Prices and rents: URA indices (2009 Q1 = 100). Activity: units transacted, launched and sold. Supply: pipeline, vacant stock, unsold approved units.
Executive condominiums: activity and supply only; there is no EC price series on data.gov.sg (it needs the URA Data Service API, which needs a free access key).
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "property")
SEG = {"Core Central Region": "ccr", "Rest of Central Region": "rcr", "Outside Central Region": "ocr"}


def _read(fn):
    return pd.read_csv(os.path.join(DATA, fn + ".csv"))


def _q(s):
    return pd.PeriodIndex(s.str.replace("-", ""), freq="Q")


def _wide(fn):
    """Wide series with columns like '20262Q' (year, quarter): returns rows=series names (stripped), columns=Period."""
    d = _read(fn).rename(columns=lambda c: c.strip())
    d["DataSeries"] = d["DataSeries"].str.strip()
    d = d.set_index("DataSeries")
    d.columns = pd.PeriodIndex([f"{c[:4]}Q{c[4]}" for c in d.columns], freq="Q")
    return d.apply(pd.to_numeric, errors="coerce").T.sort_index()


def prices():
    a = _read("ppi_all"); a["quarter"] = _q(a["quarter"]); a = a.pivot(index="quarter", columns="property_type", values="index")
    a = a.rename(columns={"All Residential": "all", "Landed": "landed", "Non-Landed": "nonlanded"})
    l = _read("ppi_nonlanded_locality"); l["quarter"] = _q(l["quarter"]); l = l.pivot(index="quarter", columns="market_segment", values="price_index").rename(columns=SEG)
    return pd.concat([a, l.add_prefix("nl_")], axis=1).sort_index()


def rents():
    r = _read("rent_index"); r["quarter"] = _q(r["quarter"])
    r["k"] = r["property_type"].map({"All Residential": "all", "Landed": "landed", "Non-Landed": "nonlanded"}) + "_" + r["locality"].map({"Whole Island": "wi", **SEG})
    out = r.pivot(index="quarter", columns="k", values="index").sort_index()
    rb = _wide("rent_index_b")                       # whole-island series from 1990 and current to the latest quarter
    rb.columns = ["all_wi", "landed_wi", "nonlanded_wi"]
    out = out.drop(columns=["all_wi", "landed_wi", "nonlanded_wi"], errors="ignore").join(rb, how="outer").sort_index()
    return out


def transactions():
    """Units transacted by sale type (new sale, resale, sub sale), whole island and by region."""
    out = {}
    for fn, nm in (("txn_all", "wi"), ("txn_ccr", "ccr"), ("txn_rcr", "rcr"), ("txn_ocr", "ocr")):
        t = _read(fn); t["quarter"] = _q(t["quarter"]); g = t.groupby(["quarter", "type_of_sale"])["units"].sum().unstack()
        g.columns = [c.lower().replace(" ", "_") for c in g.columns]; g["total"] = g.sum(axis=1); out[nm] = g
    return pd.concat(out, axis=1)


def new_sales():
    """Uncompleted units launched and sold per quarter by segment, completed units sold, and the sold/launched ratio."""
    la = _read("launched_uncompleted"); la["quarter"] = _q(la["quarter"]); la = la.pivot(index="quarter", columns="market_segment", values="units").rename(columns=SEG).add_prefix("launched_")
    so = _read("sold_uncompleted"); so["quarter"] = _q(so["quarter"]); so = so.pivot(index="quarter", columns="market_segment", values="units").rename(columns=SEG).add_prefix("sold_")
    co = _read("sold_completed"); co["quarter"] = _q(co["quarter"]); co = co.set_index("quarter")["units"].rename("sold_completed")
    d = pd.concat([la, so, co], axis=1).sort_index(); d["launched_total"] = la.sum(axis=1); d["sold_total"] = so.sum(axis=1)
    d["sold_to_launched"] = d["sold_total"] / d["launched_total"].replace(0, np.nan)
    return d


def supply():
    """Pipeline by status (landed and non-landed), available and vacant stock, unsold approved units."""
    p = _wide("supply_pipeline_b"); p.columns = [f"pipe_{i}" for i in range(len(p.columns))]
    raw = _wide("supply_pipeline_b"); cols = list(raw.columns); names = []; prefix = ""
    for c in cols:
        if c.startswith("Total Landed"): prefix = "landed"; names.append("pipe_landed_total")
        elif c.startswith("Total Non-Landed"): prefix = "nonlanded"; names.append("pipe_nonlanded_total")
        else: names.append(f"pipe_{prefix}_" + c.split(" - ")[-1].lower().replace(" ", "_").replace("-", "_"))
    raw.columns = names
    v = _wide("vacant"); v.columns = ["avail_all", "avail_landed", "avail_nonlanded", "vacant_all", "vacant_landed", "vacant_nonlanded"][: len(v.columns)]
    u = _read("unsold_approved"); u["quarter"] = _q(u["quarter"])
    u["k"] = (u["completion_status"] + "_" + u["launch_status"] + "_" + u["pre_requisites_status"]).str.lower().str.replace(" ", "_")
    un = u.groupby(["quarter", "k"])["units"].sum().unstack().add_prefix("unsold_"); un["unsold_total"] = un.sum(axis=1)
    d = pd.concat([raw, v, un], axis=1).sort_index(); d["vacancy_rate"] = d["vacant_all"] / d["avail_all"]
    return d


def executive_condos():
    """EC launches and sales, sale position (uncompleted ECs with pre-requisites for sale), and available/vacant/pipeline supply."""
    e = _read("ec_launched_sold"); e["quarter"] = _q(e["quarter"])
    pick = lambda status, sale: e[(e["ec_launched_status"] == status) & (e["type_of_sale"] == sale)].groupby("quarter")["units"].sum()
    d = pd.DataFrame({
        "ec_launched": pick("EC Launched", "na"),
        "ec_new_sold_uncompleted": pick("Uncompleted EC", "New sale"),
        "ec_new_sold_completed": pick("Completed EC", "New sale"),
        "ec_resale_under10": pick("EC Less than 10 years from TOP", "Resale"),
        "ec_resale_10plus": pick("EC 10 years or more from TOP", "Resale")})
    s = _read("ec_sale_position"); s["quarter"] = _q(s["quarter"])
    sp = s[s["ec_completion_status"].str.startswith("Uncompleted")].groupby(["quarter", "sale_status"])["units"].sum().unstack()
    d["ec_launched_and_sold"] = sp.get("Launched and Sold"); d["ec_launched_unsold"] = sp.get("Lanched but Unsold"); d["ec_not_launched_yet"] = sp.get("Not Lauched Yet")
    w = _wide("ec_vacant_pipeline"); w.columns = ["ec_available", "ec_vacant", "ec_pipeline_total", "ec_under_construction", "ec_planned_written", "ec_planned_provisional", "ec_planned_other"][: len(w.columns)]
    d = pd.concat([d, w], axis=1).sort_index(); d["ec_vacancy_rate"] = d["ec_vacant"] / d["ec_available"]
    return d


def hdb_rpi():
    """HDB Resale Price Index (1Q2009 = 100), quarterly from 1990."""
    h = _read("hdb_rpi"); h["quarter"] = _q(h["quarter"])
    return h.set_index("quarter")["index"].astype(float).sort_index()


def sources():
    import json
    return json.load(open(os.path.join(DATA, "_sources.json")))
