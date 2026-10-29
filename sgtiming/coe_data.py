"""LTA COE bidding results from data.gov.sg (Open Data Licence, no API key): quota, bids and premium by category for every bidding exercise since January 2010."""
import io, time
import pandas as pd
import requests

DATASET_ID = "d_69b3380ad7e51aff3a7dcc84eba52b8a"
POLL = "https://api-open.data.gov.sg/v1/public/api/datasets/{id}/poll-download"
META = "https://api-production.data.gov.sg/v2/public/api/datasets/{id}/metadata"


def fetch_raw():
    """Download the current CSV; returns (bytes, metadata dict)."""
    for _ in range(6):
        r = requests.get(POLL.format(id=DATASET_ID), timeout=60).json()
        if r["data"].get("status") == "DOWNLOAD_SUCCESS":
            break
        time.sleep(3)
    else:
        raise RuntimeError("data.gov.sg download did not finish")
    raw = requests.get(r["data"]["url"], timeout=120).content
    meta = requests.get(META.format(id=DATASET_ID), timeout=60).json()["data"]
    return raw, meta


def parse(raw):
    """One row per exercise and category; exercise time approximated as the 1st (round 1) or 15th (round 2) of the month."""
    d = pd.read_csv(io.BytesIO(raw))
    for c in ["quota", "bids_success", "bids_received", "premium"]:
        d[c] = pd.to_numeric(d[c].astype(str).str.replace(",", "", regex=False), errors="coerce")   # the source writes some counts as "1,007"
    d["t"] = pd.to_datetime(d["month"] + "-01") + pd.to_timedelta((d["bidding_no"] - 1) * 14, unit="D")
    return d.sort_values(["vehicle_class", "t"]).reset_index(drop=True)
