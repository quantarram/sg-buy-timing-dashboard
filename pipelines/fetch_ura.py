"""Fetch private residential transactions from the URA Data Service and write monthly aggregates by property type and type of sale (executive condominiums are a property type).
Raw transactions are not committed; only the aggregates are.  Skips quietly when URA_ACCESS_KEY is not set.  python pipelines/fetch_ura.py"""
import os, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import ura

key = ura.key_from_env()
if not key:
    print("URA_ACCESS_KEY not set: skipping"); sys.exit(0)
d = ura.private_resi_transactions(key)
print("transaction records:", len(d)); print(d["propertyType"].value_counts().to_string())
for c in ("price", "area", "noOfUnits"): d[c] = pd.to_numeric(d[c], errors="coerce")
d = d[d["noOfUnits"] == 1].copy()                                    # single-unit transactions only (bulk deals carry a total price for several units)
d["psf"] = d["price"] / (d["area"] * 10.7639)                        # area is in square metres; 1 square metre = 10.7639 square feet
cd = d["contractDate"].astype(str).str.zfill(4); d["month"] = pd.to_datetime("20" + cd.str[2:] + "-" + cd.str[:2] + "-01", errors="coerce")
d["sale"] = d["typeOfSale"].astype(str).map(ura.SALE)
g = d.groupby(["month", "propertyType", "sale"]).agg(units=("price", "size"), median_price=("price", "median"), median_psf=("psf", "median")).reset_index()
os.makedirs(os.path.join(ROOT, "data", "ura"), exist_ok=True); g.to_csv(os.path.join(ROOT, "data", "ura", "monthly_by_type.csv"), index=False)
print("monthly rows:", len(g), "| months", g["month"].min().date(), "to", g["month"].max().date())
ec = g[g["propertyType"] == "Executive Condominium"]; print("EC rows:", len(ec)); print(ec.tail(8).to_string())
