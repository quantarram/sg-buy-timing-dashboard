"""Fetch private residential transactions from the URA Data Service and write monthly aggregates by property type (including executive condominiums, if the service returns them).
Skips quietly when URA_ACCESS_KEY is not set. UNTESTED until a key exists; do not add to the daily workflow before a successful manual run.  python pipelines/fetch_ura.py"""
import os, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import ura

key = ura.key_from_env()
if not key:
    print("URA_ACCESS_KEY not set: skipping"); sys.exit(0)
d = ura.private_resi_transactions(key)
print("transactions:", len(d)); print(d["propertyType"].value_counts().to_string() if "propertyType" in d else d.columns.tolist())
d["price"] = pd.to_numeric(d["price"], errors="coerce"); d["area"] = pd.to_numeric(d["area"], errors="coerce")
d["psf"] = d["price"] / (d["area"] * 10.7639)            # area is in square metres; one square metre is 10.7639 square feet
d["month"] = pd.to_datetime(d["contractDate"].astype(str).str.zfill(4).str[2:] .radd("20") + "-" + d["contractDate"].astype(str).str.zfill(4).str[:2] + "-01", errors="coerce")
g = d.groupby(["month", "propertyType"]).agg(units=("price", "size"), median_price=("price", "median"), median_psf=("psf", "median")).reset_index()
os.makedirs(os.path.join(ROOT, "data", "ura"), exist_ok=True); g.to_csv(os.path.join(ROOT, "data", "ura", "monthly_by_type.csv"), index=False)
print(g.tail(12).to_string())
