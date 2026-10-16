"""Monthly price per square foot from the URA transaction aggregates (data/ura/monthly_by_type.csv): median over single-unit transactions, by property type and type of sale.
Medians move with the mix of projects transacted, so they are not a quality-adjusted index; new-sale medians are lumpy because they depend on which projects launch."""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "ura", "monthly_by_type.csv")
GROUPS = {"EC new sale": (("Executive Condominium",), "new sale"), "EC resale": (("Executive Condominium",), "resale"),
          "Condo new sale": (("Apartment", "Condominium"), "new sale"), "Condo resale": (("Apartment", "Condominium"), "resale")}


def available():
    return os.path.exists(PATH)


def load():
    d = pd.read_csv(PATH, parse_dates=["month"]); out = {}
    for name, (types, sale) in GROUPS.items():
        g = d[d["propertyType"].isin(types) & (d["sale"] == sale)].copy()
        # combine property types within a group: unit-weighted mean of the type medians (an approximation to the pooled median)
        g["w"] = g["units"]; agg = g.groupby("month").apply(lambda x: pd.Series(dict(units=x["units"].sum(), psf=np.average(x["median_psf"], weights=x["w"]), price=np.average(x["median_price"], weights=x["w"]))))
        out[name] = agg.sort_index()
    return out


def latest_full_month(series_dict, today):
    m = max(s.index.max() for s in series_dict.values())
    return m - pd.offsets.MonthBegin(1) if (m.year, m.month) == (today.year, today.month) else m
