"""Refresh the monthly public series from data.gov.sg into data/.  python pipelines/fetch_monthly.py"""
import os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from sgtiming import datagov  # noqa: E402

SETS = {
    "quota_premium_monthly.csv": "d_22094bf608253d36c0c63b52d852dd6e",   # quota, bids, premium by category, 2002 onward
    "newreg_vqs_monthly.csv": "d_d94cf5d839fc11a144f24ef971705d3e",      # new registrations by category
    "dereg_vqs_monthly.csv": "d_d520d6034b5e0c4f883b4e480de28f97",       # de-registrations by category
    "bank_rates_monthly.csv": "d_5fe5a4bb4a1ecc4d8a56a095832e2b24",      # SORA, government bond and bill yields
}
for fn, i in SETS.items():
    df, meta = datagov.fetch(i)
    df.to_csv(os.path.join(ROOT, "data", fn), index=False)
    print(f"{fn}: {df.shape}, source updated {str(meta.get('lastUpdatedAt'))[:10]}")
    time.sleep(3)
