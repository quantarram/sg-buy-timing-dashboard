"""Monthly panel of Category A and B COE results and their drivers, from the wide-format data.gov.sg series (rows = series, columns = '2026Sep')."""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def _wide(fn):
    d = pd.read_csv(os.path.join(DATA, fn))
    d = d.rename(columns={d.columns[0]: "series"}); d["series"] = d["series"].str.strip()
    m = d.melt(id_vars="series", var_name="month", value_name="v")
    m["month"] = pd.to_datetime(m["month"], format="%Y%b", errors="coerce")
    m["v"] = pd.to_numeric(m["v"], errors="coerce")
    return m.dropna(subset=["month"]).pivot_table(index="month", columns="series", values="v", aggfunc="first").sort_index()


def quota_panel():
    """Per month and category: quota, bids received, successful bids, premium (mean of the two rounds), prevailing premium."""
    q = _wide("quota_premium_monthly.csv"); out = {}
    for cat, pre in (("A", "Cars Up To 1600cc And 97kW"), ("B", "Cars Above 1600cc Or 97kW")):
        g = lambda tail: q.get(f"{pre}, {tail}")
        quota = g("Quota, 1st Bidding").add(g("Quota, 2nd Bidding"), fill_value=0)
        bids = g("Bids Received, 1st Bidding").add(g("Bids Received, 2nd Bidding"), fill_value=0)
        prem = pd.concat([g("Quota Premium, 1st Bidding"), g("Quota Premium, 2nd Bidding")], axis=1).mean(axis=1)
        out[cat] = pd.DataFrame({"quota": quota, "bids": bids, "premium": prem, "pqp": g("Prevailing Quota Premium, 2nd Bidding")})
    return out


def flows():
    nr = _wide("newreg_vqs_monthly.csv"); dr = _wide("dereg_vqs_monthly.csv")
    f = pd.DataFrame({"newreg_A": nr.get("Category A: Cars"), "newreg_B": nr.get("Category B: Cars"), "dereg_A": dr.get("Category A: Cars"), "dereg_B": dr.get("Category B: Cars")})
    return f


def rates():
    r = _wide("bank_rates_monthly.csv")
    return pd.DataFrame({"sora_3m": r.get("Compounded Singapore Overnight Rate Average (SORA) - 3 Month"), "sora_on": r.get("Singapore Overnight Rate Average"), "gov2y": r.get("Government Securities - 2-Year Bond Yield"), "bill1y": r.get("Government Securities - 1-Year Treasury Bills Yield")})
