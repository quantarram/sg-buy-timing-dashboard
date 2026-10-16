"""Fetch the public Singapore property series from data.gov.sg into data/property/.  python pipelines/fetch_property.py"""
import os, sys, time, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from sgtiming import datagov  # noqa: E402

SETS = {
    # prices and rents (URA, quarterly)
    "ppi_all": "d_97f8a2e995022d311c6c68cfda6d034c",
    "ppi_by_type_b": "d_da00b36ca8c831322fa0bb2a3378a476",
    "ppi_nonlanded_locality": "d_f65e490a8ad430f60a9a3d9df2bff2a0",
    "rent_index": "d_8e4c50283fb7052a391dfb746a05c853",
    "rent_index_b": "d_647dabde09e726b9eeb75e4d9cd96699",
    "rent_nonlanded_locality": "d_56b0c7f6538be69f24956634d88d82e8",
    # transactions, launches and sales
    "txn_all": "d_7c69c943d5f0d89d6a9a773d2b51f337",
    "txn_ccr": "d_c287c8be114bfa7d055b27ab2c87de83",
    "txn_rcr": "d_5785799d63a9da091f4e0b456291eeb8",
    "txn_ocr": "d_1a7823f3d31e7db4b426833833762bab",
    "launched_uncompleted": "d_70824d34defde87d88faccc5d5b1c6ea",
    "sold_uncompleted": "d_e1c5b0df62729e69c82716355ef295ba",
    "sold_completed": "d_a283de8cb3b4e80a228bf5f5e0bc4449",
    "ec_launched_sold": "d_19c79027c2e6be3c39d637151bd2188d",
    # supply
    "supply_pipeline_b": "d_055b6549444dedb341c50805d9682a41",
    "vacant": "d_01e3556fb916ca19a7e29fc39520fa78",
    "unsold_approved": "d_84d05d45049108f0fd2e99b66bd19cfe",
    "ec_vacant_pipeline": "d_361d4f4313d30951c76beaa343fd7ce1",
    "ec_sale_position": "d_8b71bc3e1386261039d7ad95efdc3328",
    # credit
}
OUT = os.path.join(ROOT, "data", "property"); os.makedirs(OUT, exist_ok=True)
info = {}
for k, i in SETS.items():
    try:
        df, meta = datagov.fetch(i)
        df.to_csv(os.path.join(OUT, k + ".csv"), index=False)
        info[k] = dict(id=i, name=meta.get("name"), rows=len(df), cols=len(df.columns), start=str(meta.get("coverageStart"))[:10], end=str(meta.get("coverageEnd"))[:10], updated=str(meta.get("lastUpdatedAt"))[:10])
        print(f"{k:26s} {df.shape} {info[k]['start']} -> {info[k]['end']} (updated {info[k]['updated']})  {meta.get('name')}")
    except Exception as e:
        print(f"{k:26s} FAILED {repr(e)[:100]}")
    time.sleep(3)
json.dump(info, open(os.path.join(OUT, "_sources.json"), "w"), indent=1)
