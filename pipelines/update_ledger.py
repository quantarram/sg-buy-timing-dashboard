"""Update the forward ledger (data/ledger/) from today's dashboard state, resolve matured outcomes, and refresh the causal replay of the base-rate forecasts.
Run after build_site.py (which writes data/ledger/today_state.json), then run build_site.py again to render the track record.  python pipelines/update_ledger.py"""
import datetime as dt, json, os, sys
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import ledger

st = json.load(open(os.path.join(ledger.LEDGER, "today_state.json")))
today = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).strftime("%Y-%m-%d")
fc, en, rs = ledger.update(today, st["active"])
retro = ledger.retrospective(ledger.series()); retro.to_csv(os.path.join(ledger.LEDGER, "retrospective.csv"), index=False)
print(f"forecasts logged {len(fc)} (resolved {int((rs['kind']=='forecast').sum())}) | entries {len(en)} (resolved horizons {int((rs['kind']=='entry').sum())}) | retrospective rows {len(retro)}")
