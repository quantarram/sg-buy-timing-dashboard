"""URA Data Service client for private residential transactions (free access key; set URA_ACCESS_KEY, never commit it).
Documented at https://eservice.ura.gov.sg/maps/api/ : a token valid for the day is generated from the access key; transactions for the past five years are downloaded in four batches split by postal district
(batch 1 = districts 01-07, batch 2 = 08-14, ...); the service updates at the end of every Tuesday and Friday. Property types include Executive Condominium. Call it from a server, not from a web page (URA's terms).
"""
import os
import pandas as pd
import requests

BASE = "https://eservice.ura.gov.sg/uraDataService"
UA = {"User-Agent": "Mozilla/5.0"}
SALE = {"1": "new sale", "2": "sub sale", "3": "resale"}


def token(key):
    r = requests.get(f"{BASE}/insertNewToken/v1", headers={"AccessKey": key, **UA}, timeout=60).json()
    if r.get("Status") != "Success":
        raise RuntimeError(f"URA token request failed: {r.get('Message')}")
    return r["Result"]


def private_resi_transactions(key):
    """All four batches as one flat table: one row per transaction record."""
    tok = token(key); rows = []
    for batch in (1, 2, 3, 4):
        r = requests.get(f"{BASE}/invokeUraDS/v1", params={"service": "PMI_Resi_Transaction", "batch": batch}, headers={"AccessKey": key, "Token": tok, **UA}, timeout=180).json()
        if r.get("Status") != "Success":
            raise RuntimeError(f"URA batch {batch} failed: {r.get('Message')}")
        for proj in r.get("Result", []):
            for t in proj.get("transaction", []):
                rows.append({"project": proj.get("project"), "street": proj.get("street"), "segment": proj.get("marketSegment"), **t})
    return pd.DataFrame(rows)


def key_from_env():
    return os.environ.get("URA_ACCESS_KEY")
