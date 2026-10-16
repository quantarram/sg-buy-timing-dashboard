"""HDB resale transactions (data.gov.sg, HDB): every registered resale since March 2012, with block and street."""
import time
import numpy as np
import pandas as pd
from . import datagov

SETS = {"2012_2014": "d_2d5ff9ea31397b66239f245f57751537", "2015_2016": "d_ea9ed51da2787afaf8e51f827c304208", "2017_on": "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"}


def fetch_all():
    frames = []
    for k, i in SETS.items():
        df, meta = datagov.fetch(i); df["src"] = k; frames.append(df); time.sleep(2)
    return pd.concat(frames, ignore_index=True)


def tidy(d):
    """One row per transaction with normalised labels."""
    d = d.copy()
    d["flat_type"] = d["flat_type"].str.upper().str.replace("MULTI GENERATION", "MULTI-GENERATION")
    d["flat_model"] = d["flat_model"].str.upper().str.strip()
    d["block"] = d["block"].astype(str).str.strip().str.upper(); d["street_name"] = d["street_name"].str.upper().str.strip(); d["town"] = d["town"].str.upper().str.strip()
    lo = d["storey_range"].str.extract(r"(\d+)\s+TO\s+(\d+)").astype(float); d["storey_mid"] = ((lo[0] + lo[1]) / 2).round().astype("Int64")
    d["resale_price"] = pd.to_numeric(d["resale_price"], errors="coerce"); d["floor_area_sqm"] = pd.to_numeric(d["floor_area_sqm"], errors="coerce")
    d["lease_commence_date"] = pd.to_numeric(d["lease_commence_date"], errors="coerce")
    d = d.dropna(subset=["resale_price", "floor_area_sqm", "month"]).drop_duplicates(subset=["month", "town", "flat_type", "block", "street_name", "storey_range", "floor_area_sqm", "flat_model", "resale_price", "lease_commence_date"], keep="first")
    return d
