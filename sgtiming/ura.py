"""URA Data Service client for private residential transactions (needs a free access key; set URA_ACCESS_KEY).

UNTESTED: the endpoints and field names below are written from memory of URA's documented flow and a third-party client (pyura), and have not been run, because no access key exists yet.
Verify against URA's documentation (https://eservice.ura.gov.sg/maps/api/) the first time a key is available. Never commit the key; it lives in the environment or a GitHub secret.
Flow: the access key generates a token valid for the day; transactions are downloaded in four batches (the third-party client says the past 3 years; unconfirmed whether executive condominiums are included).
"""
import os
import pandas as pd
import requests

BASE = "https://eservice.ura.gov.sg/uraDataService"
UA = {"User-Agent": "Mozilla/5.0"}


def token(key):
    r = requests.get(f"{BASE}/insertNewToken.action", headers={"AccessKey": key, **UA}, timeout=60).json()
    if r.get("Status") != "Success":
        raise RuntimeError(f"URA token request failed: {r.get('Message')}")
    return r["Result"]


def private_resi_transactions(key):
    """All four batches as one flat table: one row per transaction."""
    tok = token(key); rows = []
    for batch in (1, 2, 3, 4):
        r = requests.get(f"{BASE}/invokeUraDS", params={"service": "PMI_Resi_Transaction", "batch": batch}, headers={"AccessKey": key, "Token": tok, **UA}, timeout=120).json()
        for proj in r.get("Result", []):
            for t in proj.get("transaction", []):
                rows.append({"project": proj.get("project"), "street": proj.get("street"), "segment": proj.get("marketSegment"), **t})
    return pd.DataFrame(rows)


def key_from_env():
    return os.environ.get("URA_ACCESS_KEY")
