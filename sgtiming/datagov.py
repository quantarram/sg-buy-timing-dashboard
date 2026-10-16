"""Generic data.gov.sg download (open licence, no key)."""
import io, time
import pandas as pd
import requests

POLL = "https://api-open.data.gov.sg/v1/public/api/datasets/{id}/poll-download"
META = "https://api-production.data.gov.sg/v2/public/api/datasets/{id}/metadata"


def fetch(dataset_id):
    """Return (DataFrame, metadata) for a data.gov.sg dataset id."""
    for _ in range(10):
        r = requests.get(POLL.format(id=dataset_id), timeout=60).json()
        if (r.get("data") or {}).get("status") == "DOWNLOAD_SUCCESS":
            break
        time.sleep(4)
    else:
        raise RuntimeError(f"download did not finish: {dataset_id}")
    raw = requests.get(r["data"]["url"], timeout=120).content
    meta = {}
    for _ in range(4):
        try:
            m = requests.get(META.format(id=dataset_id), timeout=60).json().get("data")
        except Exception:
            m = None
        if m:
            meta = m
            break
        time.sleep(2)
    return pd.read_csv(io.BytesIO(raw)), meta
