"""Build the HDB block lookup: docs/hdb/index.json (search list) and docs/hdb/<town>.json (transactions per block and town medians).
Raw transactions are not committed; only these compact files are. Files are rewritten only when their content changes.  python pipelines/build_hdb.py"""
import json, os, re, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import hdb

OUT = os.path.join(ROOT, "docs", "hdb"); os.makedirs(OUT, exist_ok=True)
d = hdb.tidy(hdb.fetch_all())
months = sorted(d["month"].unique()); mi = {m: i for i, m in enumerate(months)}
FT = sorted(d["flat_type"].unique()); MODELS = sorted(d["flat_model"].unique())
slug = lambda t: re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def write_if_changed(path, obj):
    s = json.dumps(obj, separators=(",", ":"), sort_keys=True)
    if os.path.exists(path) and open(path, encoding="utf-8").read() == s: return False
    open(path, "w", encoding="utf-8").write(s); return True


index = []; changed = 0; total_bytes = 0
for town, g in d.groupby("town"):
    blocks = {}
    for (blk, st), x in g.groupby(["block", "street_name"]):
        x = x.sort_values("month")
        blocks[f"{blk}|{st}"] = {"lease": int(x["lease_commence_date"].mode().iloc[0]) if x["lease_commence_date"].notna().any() else None,
                                 "tx": [[mi[r.month], FT.index(r.flat_type), int(r.storey_mid) if pd.notna(r.storey_mid) else 0, int(round(r.floor_area_sqm)), int(r.resale_price), MODELS.index(r.flat_model)] for r in x.itertuples()]}
        index.append([blk, st, town, len(x), mi[x["month"].iloc[-1]]])
    med = {}
    for ft, x in g.groupby("flat_type"):
        s = x.groupby("month")["resale_price"].agg(["median", "size"]); med[ft] = [int(s.loc[m, "median"]) if (m in s.index and s.loc[m, "size"] >= 3) else None for m in months]
    obj = {"town": town, "blocks": blocks, "town_med": med}
    changed += write_if_changed(os.path.join(OUT, slug(town) + ".json"), obj); total_bytes += os.path.getsize(os.path.join(OUT, slug(town) + ".json"))
meta = {"months": months, "flat_types": FT, "models": MODELS, "towns": {t: slug(t) for t in sorted(d["town"].unique())}, "built": pd.Timestamp.utcnow().strftime("%Y-%m-%d"), "n_tx": int(len(d)), "n_blocks": len(index)}
index.sort()
changed += write_if_changed(os.path.join(OUT, "index.json"), {"meta": {k: v for k, v in meta.items() if k != "built"}, "blocks": index})
print(f"transactions {len(d):,} | blocks {len(index):,} | towns {d['town'].nunique()} | months {months[0]} to {months[-1]} | files changed {changed} | shard bytes {total_bytes/1e6:.1f} MB | index {os.path.getsize(os.path.join(OUT,'index.json'))/1e3:.0f} KB")
