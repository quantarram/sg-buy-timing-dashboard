"""Refresh data/coe_results.csv from data.gov.sg and print what changed.  python pipelines/fetch_coe.py"""
import io, os, sys
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from sgtiming import coe_data  # noqa: E402

OUT = os.path.join(ROOT, "data", "coe_results.csv")
raw, meta = coe_data.fetch_raw()
old = pd.read_csv(OUT) if os.path.exists(OUT) else None
open(OUT, "wb").write(raw)
new = pd.read_csv(io.BytesIO(raw))
print(f"rows {len(new)} (was {len(old) if old is not None else 0}); last exercise {new['month'].iloc[-1]} round {new['bidding_no'].iloc[-1]}; source updated {meta.get('lastUpdatedAt')}")
